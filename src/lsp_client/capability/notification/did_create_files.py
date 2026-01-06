from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol, override, runtime_checkable

from lsp_client.protocol import CapabilityClientProtocol, WorkspaceCapabilityProtocol
from lsp_client.utils.types import lsp_type


@runtime_checkable
class WithNotifyDidCreateFiles(
    WorkspaceCapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `workspace/didCreateFiles` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_didCreateFiles
    """

    @override
    @classmethod
    def iter_methods(cls) -> Iterator[str]:
        yield from super().iter_methods()
        yield from (lsp_type.WORKSPACE_DID_CREATE_FILES,)

    @override
    @classmethod
    def register_workspace_capability(
        cls, cap: lsp_type.WorkspaceClientCapabilities
    ) -> None:
        super().register_workspace_capability(cap)
        if cap.file_operations is None:
            cap.file_operations = lsp_type.FileOperationClientCapabilities()
        cap.file_operations.did_create = True

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)

    async def _notify_did_create_files(
        self, params: lsp_type.CreateFilesParams
    ) -> None:
        return await self.notify(lsp_type.DidCreateFilesNotification(params=params))

    async def notify_did_create_files(self, uris: list[str]) -> None:
        """
        Notify server that files have been created.

        Args:
            uris: List of file URIs that were created
        """
        return await self._notify_did_create_files(
            lsp_type.CreateFilesParams(
                files=[lsp_type.FileCreate(uri=uri) for uri in uris]
            )
        )
