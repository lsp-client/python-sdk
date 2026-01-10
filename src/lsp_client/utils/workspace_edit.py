from __future__ import annotations

import shutil
from collections.abc import Iterator, Mapping, Sequence
from contextlib import suppress

import anyio
import anyio.to_thread
from attrs import define
from loguru import logger

from lsp_client.exception import EditApplicationError, VersionMismatchError
from lsp_client.protocol import DocumentEditProtocol
from lsp_client.utils.types import lsp_type
from lsp_client.utils.uri import from_local_uri

type AnyTextEdit = (
    lsp_type.TextEdit | lsp_type.AnnotatedTextEdit | lsp_type.SnippetTextEdit
)


def get_edit_text(edit: AnyTextEdit) -> str:
    """Extract text from different edit types."""
    match edit:
        case lsp_type.SnippetTextEdit(snippet=snippet):
            # For SnippetTextEdit, use the snippet as plain text
            return snippet.value
        case _:
            return edit.new_text


def apply_text_edits(content: str, edits: Sequence[AnyTextEdit]) -> str:
    """
    Apply a list of text edits to content.

    Args:
        content: Original document content
        edits: List of text edits to apply

    Returns:
        Updated content after applying all edits

    Note:
        Edits can be provided in any order. They are automatically sorted in
        reverse order (last to first) to maintain correct positions during
        application.
    """
    lines = content.splitlines(keepends=True)

    # Sort edits in reverse order to apply from end to start
    sorted_edits = sorted(
        edits, key=lambda e: (e.range.start.line, e.range.start.character), reverse=True
    )

    for edit in sorted_edits:
        new_text = get_edit_text(edit)
        start_line = edit.range.start.line
        start_char = edit.range.start.character
        end_line = edit.range.end.line
        end_char = edit.range.end.character

        # Handle start line
        if start_line >= len(lines):
            # Beyond end of file, append newlines if needed
            while len(lines) <= start_line:
                lines.append("\n")
            lines[start_line] = new_text
            continue

        start_line_content = lines[start_line]

        # Handle end line
        end_line_content = "" if end_line >= len(lines) else lines[end_line]

        # Build new content
        if start_line == end_line:
            # Single line edit
            new_line = (
                start_line_content[:start_char]
                + new_text
                + start_line_content[end_char:]
            )
            lines[start_line] = new_line
        else:
            # Multi-line edit
            new_line = (
                start_line_content[:start_char] + new_text + end_line_content[end_char:]
            )
            lines[start_line] = new_line
            # Remove lines in between
            if end_line < len(lines):
                del lines[start_line + 1 : end_line + 1]

    return "".join(lines)


def iter_text_document_edits(
    edit: lsp_type.WorkspaceEdit,
) -> Iterator[tuple[str, Sequence[AnyTextEdit]]]:
    """
    Iterate over text document edits in a WorkspaceEdit.

    This helper unifies the two formats of WorkspaceEdit:
    1. documentChanges (modern, supports resource operations)
    2. changes (legacy, URI to TextEdit[] mapping)

    Returns:
        Iterator of (uri, edits) tuples
    """
    if edit.document_changes:
        for change in edit.document_changes:
            match change:
                case lsp_type.TextDocumentEdit(
                    text_document=text_document, edits=edits
                ):
                    yield text_document.uri, edits
                case _:
                    continue
    elif edit.changes:
        yield from edit.changes.items()


@define
class WorkspaceEditApplicator:
    """
    Applies workspace edits to documents with version validation.

    Attributes:
        client: Client instance with document state and file I/O operations
    """

    client: DocumentEditProtocol

    async def apply_workspace_edit(self, edit: lsp_type.WorkspaceEdit) -> None:
        """
        Apply workspace edit to documents.

        Args:
            edit: Workspace edit to apply

        Raises:
            EditApplicationError: If edit cannot be applied due to business logic
            OSError: If file I/O operations fail
            ValueError: If edit contains invalid data
        """
        if edit.document_changes:
            await self._apply_document_changes(edit.document_changes)
        elif edit.changes:
            await self._apply_changes(edit.changes)

    async def _apply_document_changes(
        self,
        changes: Sequence[
            lsp_type.TextDocumentEdit
            | lsp_type.CreateFile
            | lsp_type.RenameFile
            | lsp_type.DeleteFile
        ],
    ) -> None:
        """Apply document changes with version validation."""
        for change in changes:
            match change:
                case lsp_type.TextDocumentEdit():
                    await self._apply_text_document_edit(change)
                case lsp_type.CreateFile():
                    await self._apply_create_file(change)
                case lsp_type.RenameFile():
                    await self._apply_rename_file(change)
                case lsp_type.DeleteFile():
                    await self._apply_delete_file(change)

    async def _apply_text_document_edit(self, edit: lsp_type.TextDocumentEdit) -> None:
        """Apply text document edit with version validation."""
        uri = edit.text_document.uri
        expected_version = edit.text_document.version

        # Validate version if specified
        if expected_version is not None:
            try:
                actual_version = self.client.get_document_state().get_version(uri)
            except KeyError as e:
                raise EditApplicationError(
                    message=f"Document {uri} not open in client",
                    uri=uri,
                ) from e

            if actual_version != expected_version:
                raise VersionMismatchError(
                    message=(
                        f"Version mismatch for {uri}: "
                        f"expected {expected_version}, got {actual_version}"
                    ),
                    uri=uri,
                    expected_version=expected_version,
                    actual_version=actual_version,
                )

        # Read, apply, and write edits
        file_path = self.client.from_uri(uri, relative=False)
        content = await self.client.read_file(file_path)
        new_content = apply_text_edits(content, edit.edits)
        await self.client.write_file(uri, new_content)

        # Update document state if tracked
        with suppress(KeyError):
            _ = self.client.get_document_state().update_content(uri, new_content)

    async def _apply_changes(
        self, changes: Mapping[str, Sequence[lsp_type.TextEdit]]
    ) -> None:
        """Apply changes map (deprecated format)."""
        for uri, edits in changes.items():
            # Read, apply, and write edits
            file_path = self.client.from_uri(uri, relative=False)
            content = await self.client.read_file(file_path)
            new_content = apply_text_edits(content, edits)
            await self.client.write_file(uri, new_content)

            # Update document state if tracked
            with suppress(KeyError):
                _ = self.client.get_document_state().update_content(uri, new_content)

    async def _apply_create_file(self, change: lsp_type.CreateFile) -> None:
        """Apply CreateFile resource operation."""
        uri = change.uri
        path = from_local_uri(uri)
        file_path = anyio.Path(path)

        # Check if file exists
        if await file_path.exists():
            options = change.options
            if options and options.overwrite:
                # Overwrite is allowed, continue
                pass
            elif options and options.ignore_if_exists:
                # Ignore the create operation
                logger.debug(
                    f"Skipping CreateFile for {uri}: file exists and ignoreIfExists is true"
                )
                return
            else:
                # Default behavior: fail if file exists
                raise EditApplicationError(
                    message=f"File {uri} already exists and overwrite is not allowed",
                    uri=uri,
                )

        # Create parent directories if needed
        parent = file_path.parent
        if parent and not await parent.exists():
            await parent.mkdir(parents=True, exist_ok=True)

        # Create the file
        _ = await file_path.write_text("")
        logger.debug(f"Created file: {uri}")

    async def _apply_rename_file(self, change: lsp_type.RenameFile) -> None:
        """Apply RenameFile resource operation."""
        old_uri = change.old_uri
        new_uri = change.new_uri
        old_path = anyio.Path(from_local_uri(old_uri))
        new_path = anyio.Path(from_local_uri(new_uri))

        # Check if old file exists
        if not await old_path.exists():
            raise EditApplicationError(
                message=f"Source file {old_uri} does not exist",
                uri=old_uri,
            )

        # Check if new file exists
        if await new_path.exists():
            options = change.options
            if options and options.overwrite:
                # Overwrite is allowed, delete the target
                await new_path.unlink()
            elif options and options.ignore_if_exists:
                # Ignore the rename operation
                logger.debug(
                    f"Skipping RenameFile {old_uri} -> {new_uri}: target exists and ignoreIfExists is true"
                )
                return
            else:
                # Default behavior: fail if target exists
                raise EditApplicationError(
                    message=f"Target file {new_uri} already exists and overwrite is not allowed",
                    uri=new_uri,
                )

        # Create parent directories for target if needed
        parent = new_path.parent
        if parent and not await parent.exists():
            await parent.mkdir(parents=True, exist_ok=True)

        # Perform the rename
        _ = await old_path.rename(new_path)
        logger.debug(f"Renamed file: {old_uri} -> {new_uri}")

        # Update document state if tracked
        with suppress(KeyError):
            content = self.client.get_document_state().get_content(old_uri)
            version = self.client.get_document_state().get_version(old_uri)
            self.client.get_document_state().unregister(old_uri)
            self.client.get_document_state().register(new_uri, content, version=version)

    async def _apply_delete_file(self, change: lsp_type.DeleteFile) -> None:
        """Apply DeleteFile resource operation."""
        uri = change.uri
        path = anyio.Path(from_local_uri(uri))

        # Check if file exists
        if not await path.exists():
            if change.options and change.options.ignore_if_not_exists:
                # Ignore the delete operation
                logger.debug(
                    f"Skipping DeleteFile for {uri}: file does not exist and ignoreIfNotExists is true"
                )
                return
            # Default behavior: fail if file doesn't exist
            raise EditApplicationError(
                message=f"File {uri} does not exist",
                uri=uri,
            )

        # Handle directory or file
        if await path.is_dir():
            if change.options and change.options.recursive:
                # Recursively delete directory
                await anyio.to_thread.run_sync(shutil.rmtree, str(path))
                logger.debug(f"Deleted directory recursively: {uri}")
            else:
                # Only delete empty directories
                try:
                    await path.rmdir()
                    logger.debug(f"Deleted empty directory: {uri}")
                except OSError as e:
                    raise EditApplicationError(
                        message=f"Directory {uri} is not empty and recursive is not set",
                        uri=uri,
                    ) from e
        else:
            # Delete file
            await path.unlink()
            logger.debug(f"Deleted file: {uri}")

        # Update document state if tracked
        with suppress(KeyError):
            self.client.get_document_state().unregister(uri)
