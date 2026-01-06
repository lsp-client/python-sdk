from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol, override, runtime_checkable

from loguru import logger

from lsp_client.exception import EditApplicationError
from lsp_client.protocol import (
    CapabilityClientProtocol,
    ServerRequestHook,
    ServerRequestHookProtocol,
    ServerRequestHookRegistry,
    WorkspaceCapabilityProtocol,
)
from lsp_client.utils.types import lsp_type
from lsp_client.utils.workspace_edit import (
    DocumentEditProtocol,
    WorkspaceEditApplicator,
)


@runtime_checkable
class WithRespondApplyEdit(
    WorkspaceCapabilityProtocol,
    ServerRequestHookProtocol,
    CapabilityClientProtocol,
    DocumentEditProtocol,
    Protocol,
):
    """
    `workspace/applyEdit` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_applyEdit

    This capability implements workspace edit application with text document edits
    and version validation.

    **Current Implementation (Phase 1):**
    - Text document edits with version validation
    - Support for both `documentChanges` and deprecated `changes` format

    **Advertised but Not Yet Implemented:**
    Resource operations (Create, Rename, Delete) are advertised in the client
    capabilities for forward compatibility, but will raise `EditApplicationError`
    if requested by the server. Full support for these operations is planned for
    Phase 3 of the version management implementation.
    """

    @override
    @classmethod
    def iter_methods(cls) -> Iterator[str]:
        yield from super().iter_methods()
        yield lsp_type.WORKSPACE_APPLY_EDIT

    @override
    @classmethod
    def register_workspace_capability(
        cls, cap: lsp_type.WorkspaceClientCapabilities
    ) -> None:
        super().register_workspace_capability(cap)
        cap.apply_edit = True
        cap.workspace_edit = lsp_type.WorkspaceEditClientCapabilities(
            document_changes=True,
            resource_operations=[
                lsp_type.ResourceOperationKind.Create,
                lsp_type.ResourceOperationKind.Rename,
                lsp_type.ResourceOperationKind.Delete,
            ],
            failure_handling=lsp_type.FailureHandlingKind.Undo,
        )

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)

    async def _respond_apply_edit(
        self, params: lsp_type.ApplyWorkspaceEditParams
    ) -> lsp_type.ApplyWorkspaceEditResult:
        logger.debug("Responding to workspace/applyEdit request")

        applicator = WorkspaceEditApplicator(client=self)
        try:
            await applicator.apply_workspace_edit(params.edit)
            return lsp_type.ApplyWorkspaceEditResult(applied=True)
        except EditApplicationError as e:
            logger.error(f"Failed to apply workspace edit: {e.message}")
            return lsp_type.ApplyWorkspaceEditResult(
                applied=False, failure_reason=e.message
            )
        except (OSError, ValueError) as e:
            logger.error(f"I/O error applying workspace edit: {e}")
            return lsp_type.ApplyWorkspaceEditResult(
                applied=False, failure_reason=str(e)
            )

    async def apply_workspace_edit(self, edit: lsp_type.WorkspaceEdit) -> None:
        """
        Apply workspace edit to documents.

        This is a convenience method for applying workspace edits obtained from
        LSP requests (e.g., from request_rename_edits).

        Args:
            edit: Workspace edit to apply

        Raises:
            EditApplicationError: If edit cannot be applied due to business logic
                (e.g., version mismatch, file not found)
            OSError: If file I/O operations fail
            ValueError: If edit contains invalid data

        Example:
            >>> edits = await client.request_rename_edits(file, pos, "new_name")
            >>> if edits:
            >>>     try:
            >>>         await client.apply_workspace_edit(edits)
            >>>         print("Changes applied successfully")
            >>>     except EditApplicationError as e:
            >>>         print(f"Failed to apply: {e.message}")
        """
        applicator = WorkspaceEditApplicator(client=self)
        await applicator.apply_workspace_edit(edit)

    async def respond_apply_edit(
        self, req: lsp_type.ApplyWorkspaceEditRequest
    ) -> lsp_type.ApplyWorkspaceEditResponse:
        return lsp_type.ApplyWorkspaceEditResponse(
            id=req.id,
            result=await self._respond_apply_edit(req.params),
        )

    @override
    def register_server_request_hooks(
        self, registry: ServerRequestHookRegistry
    ) -> None:
        super().register_server_request_hooks(registry)

        registry.register(
            lsp_type.WORKSPACE_APPLY_EDIT,
            ServerRequestHook(
                cls=lsp_type.ApplyWorkspaceEditRequest,
                execute=self.respond_apply_edit,
            ),
        )
