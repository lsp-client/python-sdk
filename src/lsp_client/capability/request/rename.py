from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol, override, runtime_checkable

from lsp_client.jsonrpc.id import jsonrpc_uuid
from lsp_client.protocol import CapabilityClientProtocol, TextDocumentCapabilityProtocol
from lsp_client.utils.types import AnyPath, Position, lsp_type
from lsp_client.utils.workspace_edit import (
    DocumentEditProtocol,
    WorkspaceEditApplicator,
)


@runtime_checkable
class WithRequestRename(
    TextDocumentCapabilityProtocol,
    CapabilityClientProtocol,
    DocumentEditProtocol,
    Protocol,
):
    """
    - `textDocument/rename` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_rename
    - `textDocument/prepareRename` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_prepareRename
    """

    @override
    @classmethod
    def iter_methods(cls) -> Iterator[str]:
        yield from super().iter_methods()
        yield from (
            lsp_type.TEXT_DOCUMENT_RENAME,
            lsp_type.TEXT_DOCUMENT_PREPARE_RENAME,
        )

    @override
    @classmethod
    def register_text_document_capability(
        cls, cap: lsp_type.TextDocumentClientCapabilities
    ) -> None:
        super().register_text_document_capability(cap)
        cap.rename = lsp_type.RenameClientCapabilities(
            prepare_support=True,
        )

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)
        assert cap.rename_provider

    async def _request_prepare_rename(
        self, params: lsp_type.PrepareRenameParams
    ) -> lsp_type.PrepareRenameResult | None:
        return await self.request(
            lsp_type.PrepareRenameRequest(
                id=jsonrpc_uuid(),
                params=params,
            ),
            schema=lsp_type.PrepareRenameResponse,
        )

    async def _request_rename(
        self, params: lsp_type.RenameParams
    ) -> lsp_type.RenameResult | None:
        return await self.request(
            lsp_type.RenameRequest(
                id=jsonrpc_uuid(),
                params=params,
            ),
            schema=lsp_type.RenameResponse,
        )

    async def request_prepare_rename(
        self, file_path: AnyPath, position: Position
    ) -> lsp_type.PrepareRenameResult | None:
        """
        Prepare for a rename operation at the given position.

        Returns:
            Range and placeholder text for rename, or None if rename not possible
        """
        async with self.open_files(file_path):
            return await self._request_prepare_rename(
                lsp_type.PrepareRenameParams(
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                )
            )

    async def request_rename_edits(
        self, file_path: AnyPath, position: Position, new_name: str
    ) -> lsp_type.WorkspaceEdit | None:
        """
        Get workspace edits for renaming the symbol at the given position.

        This method returns the WorkspaceEdit without applying it, allowing
        users to preview the changes before committing.

        Args:
            file_path: Path to the file containing the symbol
            position: Position of the symbol to rename
            new_name: New name for the symbol

        Returns:
            WorkspaceEdit containing all rename changes, or None if rename
            is not possible at this position

        Example:
            >>> edits = await client.request_rename_edits("file.py", pos, "new_name")
            >>> if edits:
            >>>     # Preview changes
            >>>     for uri, text_edits in edits.changes.items():
            >>>         print(f"File: {uri}, {len(text_edits)} changes")
            >>>     # Apply when ready
            >>>     applicator = WorkspaceEditApplicator(client=client)
            >>>     await applicator.apply_workspace_edit(edits)
        """
        async with self.open_files(file_path):
            return await self._request_rename(
                lsp_type.RenameParams(
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                    new_name=new_name,
                )
            )

    async def apply_workspace_edit(self, edit: lsp_type.WorkspaceEdit) -> None:
        """
        Apply workspace edit to documents.

        This is a helper method that provides a convenient way to apply
        workspace edits returned from request_rename_edits().

        Args:
            edit: Workspace edit to apply

        Raises:
            EditApplicationError: If edit cannot be applied
            OSError: If file I/O operations fail

        Example:
            >>> edits = await client.request_rename_edits(file, pos, "new_name")
            >>> if edits:
            >>>     try:
            >>>         await client.apply_workspace_edit(edits)
            >>>         print("Changes applied")
            >>>     except EditApplicationError as e:
            >>>         print(f"Failed: {e.message}")
        """
        applicator = WorkspaceEditApplicator(client=self)
        await applicator.apply_workspace_edit(edit)

    async def request_rename(
        self, file_path: AnyPath, position: Position, new_name: str
    ) -> bool:
        """
        Rename the symbol at the given position and apply changes immediately.

        This is a convenience method that gets the workspace edit and applies it.
        For previewing changes before applying, use request_rename_edits() instead.

        Args:
            file_path: Path to the file containing the symbol
            position: Position of the symbol to rename
            new_name: New name for the symbol

        Returns:
            True if rename was applied successfully, False if rename is not
            possible at this position

        Raises:
            EditApplicationError: If rename edit cannot be applied
            OSError: If file I/O operations fail
        """
        workspace_edit = await self.request_rename_edits(file_path, position, new_name)

        if workspace_edit is None:
            return False

        await self.apply_workspace_edit(workspace_edit)
        return True
