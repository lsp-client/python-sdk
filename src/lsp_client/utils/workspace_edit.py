from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import suppress
from pathlib import Path
from typing import Protocol, runtime_checkable

from attrs import define
from loguru import logger

from lsp_client.client.document_state import DocumentStateManager
from lsp_client.exception import EditApplicationError, VersionMismatchError
from lsp_client.utils.types import lsp_type


@runtime_checkable
class DocumentEditProtocol(Protocol):
    """Protocol for objects that can apply document edits."""

    _document_state: DocumentStateManager

    async def read_file(self, file_path: str | Path) -> str:
        """Read file content by path."""
        ...

    async def write_file(self, uri: str, content: str) -> None:
        """Write file content by URI."""
        ...

    def from_uri(self, uri: str, *, relative: bool = True) -> Path:
        """Convert a URI to a path."""
        ...


def _get_edit_text(
    edit: lsp_type.TextEdit | lsp_type.AnnotatedTextEdit | lsp_type.SnippetTextEdit,
) -> str:
    """Extract text from different edit types."""
    if isinstance(edit, lsp_type.SnippetTextEdit):
        # For SnippetTextEdit, use the snippet as plain text
        return edit.snippet.value
    return edit.new_text


def apply_text_edits(
    content: str,
    edits: Sequence[
        lsp_type.TextEdit | lsp_type.AnnotatedTextEdit | lsp_type.SnippetTextEdit
    ],
) -> str:
    """
    Apply a list of text edits to content.

    Args:
        content: Original document content
        edits: List of text edits to apply

    Returns:
        Updated content after applying all edits

    Note:
        Edits must be sorted in reverse order (last to first) to maintain
        correct positions during application.
    """
    lines = content.splitlines(keepends=True)

    # Sort edits in reverse order to apply from end to start
    sorted_edits = sorted(
        edits, key=lambda e: (e.range.start.line, e.range.start.character), reverse=True
    )

    for edit in sorted_edits:
        new_text = _get_edit_text(edit)
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


@define
class WorkspaceEditApplicator:
    """
    Applies workspace edits to documents with version validation.

    Attributes:
        client: Client instance with document state and file I/O operations
    """

    client: DocumentEditProtocol

    async def apply_workspace_edit(
        self, edit: lsp_type.WorkspaceEdit
    ) -> tuple[bool, str | None]:
        """
        Apply workspace edit to documents.

        Args:
            edit: Workspace edit to apply

        Returns:
            Tuple of (success, failure_reason)
            - success: True if edit was applied successfully
            - failure_reason: None on success, error message on failure
        """
        try:
            if edit.document_changes:
                await self._apply_document_changes(edit.document_changes)
            elif edit.changes:
                await self._apply_changes(edit.changes)

            return True, None
        except EditApplicationError as e:
            logger.error(f"Failed to apply workspace edit: {e.message}")
            return False, e.message
        except (OSError, ValueError) as e:
            logger.error(f"I/O error applying workspace edit: {e}")
            return False, str(e)

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
                    raise EditApplicationError(
                        message="CreateFile not yet supported",
                        uri=change.uri,
                    )
                case lsp_type.RenameFile():
                    raise EditApplicationError(
                        message="RenameFile not yet supported",
                        uri=change.old_uri,
                    )
                case lsp_type.DeleteFile():
                    raise EditApplicationError(
                        message="DeleteFile not yet supported",
                        uri=change.uri,
                    )

    async def _apply_text_document_edit(self, edit: lsp_type.TextDocumentEdit) -> None:
        """Apply text document edit with version validation."""
        uri = edit.text_document.uri
        expected_version = edit.text_document.version

        # Validate version if specified
        if expected_version is not None:
            try:
                actual_version = self.client._document_state.get_version(uri)
            except KeyError as e:
                raise EditApplicationError(
                    message=f"Document {uri} not open in client",
                    uri=uri,
                ) from e

            if actual_version != expected_version:
                raise VersionMismatchError(
                    message=f"Version mismatch for {uri}: expected {expected_version}, got {actual_version}",
                    uri=uri,
                    expected_version=expected_version,
                    actual_version=actual_version,
                )

        # Read, apply, and write edits
        file_path = self.client.from_uri(uri, relative=False)
        content = await self.client.read_file(file_path)
        new_content = apply_text_edits(content, edit.edits)
        await self.client.write_file(uri, new_content)

        # Update document state
        self.client._document_state.update_content(uri, new_content)

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
                self.client._document_state.update_content(uri, new_content)
