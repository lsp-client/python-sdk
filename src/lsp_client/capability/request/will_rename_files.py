from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol, override, runtime_checkable

from lsp_client.jsonrpc.id import jsonrpc_uuid
from lsp_client.protocol import CapabilityClientProtocol, WorkspaceCapabilityProtocol
from lsp_client.utils.types import lsp_type

from ._workspace_edit_mixin import WithApplyWorkspaceEdit


@runtime_checkable
class WithRequestWillRenameFiles(
    WorkspaceCapabilityProtocol,
    CapabilityClientProtocol,
    WithApplyWorkspaceEdit,
    Protocol,
):
    """
    `workspace/willRenameFiles` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_willRenameFiles
    """

    @override
    @classmethod
    def iter_methods(cls) -> Iterator[str]:
        yield from super().iter_methods()
        yield from (lsp_type.WORKSPACE_WILL_RENAME_FILES,)

    @override
    @classmethod
    def register_workspace_capability(
        cls, cap: lsp_type.WorkspaceClientCapabilities
    ) -> None:
        super().register_workspace_capability(cap)
        if cap.file_operations is None:
            cap.file_operations = lsp_type.FileOperationClientCapabilities()
        cap.file_operations.will_rename = True

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)
        # Server capability is optional
        if cap.workspace and cap.workspace.file_operations:
            return

    async def _request_will_rename_files(
        self, params: lsp_type.RenameFilesParams
    ) -> lsp_type.WorkspaceEdit | None:
        return await self.request(
            lsp_type.WillRenameFilesRequest(
                id=jsonrpc_uuid(),
                params=params,
            ),
            schema=lsp_type.WillRenameFilesResponse,
        )

    async def request_will_rename_files(
        self, file_renames: list[tuple[str, str]]
    ) -> lsp_type.WorkspaceEdit | None:
        """
        Request workspace edits before renaming files.

        Args:
            file_renames: List of (old_uri, new_uri) tuples

        Returns:
            WorkspaceEdit to apply before renaming files, or None
        """
        return await self._request_will_rename_files(
            lsp_type.RenameFilesParams(
                files=[
                    lsp_type.FileRename(old_uri=old, new_uri=new)
                    for old, new in file_renames
                ]
            )
        )
