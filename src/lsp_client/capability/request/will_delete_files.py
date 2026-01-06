from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol, override, runtime_checkable

from lsp_client.jsonrpc.id import jsonrpc_uuid
from lsp_client.protocol import CapabilityClientProtocol, WorkspaceCapabilityProtocol
from lsp_client.utils.types import lsp_type

from ._workspace_edit_mixin import WithApplyWorkspaceEdit


@runtime_checkable
class WithRequestWillDeleteFiles(
    WorkspaceCapabilityProtocol,
    CapabilityClientProtocol,
    WithApplyWorkspaceEdit,
    Protocol,
):
    """
    `workspace/willDeleteFiles` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_willDeleteFiles
    """

    @override
    @classmethod
    def iter_methods(cls) -> Iterator[str]:
        yield from super().iter_methods()
        yield from (lsp_type.WORKSPACE_WILL_DELETE_FILES,)

    @override
    @classmethod
    def register_workspace_capability(
        cls, cap: lsp_type.WorkspaceClientCapabilities
    ) -> None:
        super().register_workspace_capability(cap)
        if cap.file_operations is None:
            cap.file_operations = lsp_type.FileOperationClientCapabilities()
        cap.file_operations.will_delete = True

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)
        # Server capability is optional
        if cap.workspace and cap.workspace.file_operations:
            return

    async def _request_will_delete_files(
        self, params: lsp_type.DeleteFilesParams
    ) -> lsp_type.WorkspaceEdit | None:
        return await self.request(
            lsp_type.WillDeleteFilesRequest(
                id=jsonrpc_uuid(),
                params=params,
            ),
            schema=lsp_type.WillDeleteFilesResponse,
        )

    async def request_will_delete_files(
        self, uris: list[str]
    ) -> lsp_type.WorkspaceEdit | None:
        """
        Request workspace edits before deleting files.

        Args:
            uris: List of file URIs to be deleted

        Returns:
            WorkspaceEdit to apply before deleting files, or None
        """
        return await self._request_will_delete_files(
            lsp_type.DeleteFilesParams(
                files=[lsp_type.FileDelete(uri=uri) for uri in uris]
            )
        )
