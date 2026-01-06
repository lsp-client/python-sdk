from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol, override, runtime_checkable

from lsp_client.protocol import CapabilityClientProtocol, WorkspaceCapabilityProtocol
from lsp_client.utils.types import lsp_type


@runtime_checkable
class WithNotifyDidRenameFiles(
    WorkspaceCapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `workspace/didRenameFiles` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_didRenameFiles
    """

    @override
    @classmethod
    def iter_methods(cls) -> Iterator[str]:
        yield from super().iter_methods()
        yield from (lsp_type.WORKSPACE_DID_RENAME_FILES,)

    @override
    @classmethod
    def register_workspace_capability(
        cls, cap: lsp_type.WorkspaceClientCapabilities
    ) -> None:
        super().register_workspace_capability(cap)
        if cap.file_operations is None:
            cap.file_operations = lsp_type.FileOperationClientCapabilities()
        cap.file_operations.did_rename = True

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)

    async def _notify_did_rename_files(
        self, params: lsp_type.RenameFilesParams
    ) -> None:
        return await self.notify(lsp_type.DidRenameFilesNotification(params=params))

    async def notify_did_rename_files(
        self, file_renames: list[tuple[str, str]]
    ) -> None:
        """
        Notify server that files have been renamed.

        Args:
            file_renames: List of (old_uri, new_uri) tuples
        """
        return await self._notify_did_rename_files(
            lsp_type.RenameFilesParams(
                files=[
                    lsp_type.FileRename(old_uri=old, new_uri=new)
                    for old, new in file_renames
                ]
            )
        )
