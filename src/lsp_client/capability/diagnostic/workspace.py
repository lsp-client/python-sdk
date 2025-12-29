from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol, override, runtime_checkable

from lsp_client.jsonrpc.id import jsonrpc_uuid
from lsp_client.protocol import (
    CapabilityClientProtocol,
    ServerRequestHook,
    ServerRequestHookProtocol,
    ServerRequestHookRegistry,
    WorkspaceCapabilityProtocol,
)
from lsp_client.utils.types import lsp_type


@runtime_checkable
class WithWorkspaceDiagnostic(
    WorkspaceCapabilityProtocol,
    ServerRequestHookProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `workspace/diagnostic` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_diagnostic
    `workspace/diagnostic/refresh` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#diagnostic_refresh
    """

    @override
    @classmethod
    def iter_methods(cls) -> Iterator[str]:
        yield from super().iter_methods()
        yield lsp_type.WORKSPACE_DIAGNOSTIC
        yield lsp_type.WORKSPACE_DIAGNOSTIC_REFRESH

    @override
    @classmethod
    def register_workspace_capability(
        cls, cap: lsp_type.WorkspaceClientCapabilities
    ) -> None:
        super().register_workspace_capability(cap)
        cap.diagnostics = lsp_type.DiagnosticWorkspaceClientCapabilities(
            refresh_support=True,
        )

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)
        assert cap.diagnostic_provider
        assert cap.diagnostic_provider.workspace_diagnostics

    async def _request_workspace_diagnostic(
        self, params: lsp_type.WorkspaceDiagnosticParams
    ) -> lsp_type.WorkspaceDiagnosticReport:
        return await self.request(
            lsp_type.WorkspaceDiagnosticRequest(
                id=jsonrpc_uuid(),
                params=params,
            ),
            schema=lsp_type.WorkspaceDiagnosticResponse,
        )

    async def request_workspace_diagnostic(
        self,
        *,
        identifier: str | None = None,
        previous_result_ids: list[lsp_type.PreviousResultId] | None = None,
    ) -> lsp_type.WorkspaceDiagnosticReport | None:
        """
        `workspace/diagnostic` - Request diagnostic reports for the whole workspace.
        """
        return await self._request_workspace_diagnostic(
            lsp_type.WorkspaceDiagnosticParams(
                identifier=identifier,
                previous_result_ids=previous_result_ids or [],
            )
        )

    async def _respond_diagnostic_refresh(self, params: None) -> None:
        return None

    async def respond_diagnostic_refresh(
        self, req: lsp_type.DiagnosticRefreshRequest
    ) -> lsp_type.DiagnosticRefreshResponse:
        return lsp_type.DiagnosticRefreshResponse(
            id=req.id,
            result=await self._respond_diagnostic_refresh(req.params),
        )

    @override
    def register_server_request_hooks(
        self, registry: ServerRequestHookRegistry
    ) -> None:
        super().register_server_request_hooks(registry)
        registry.register(
            lsp_type.WORKSPACE_DIAGNOSTIC_REFRESH,
            ServerRequestHook(
                cls=lsp_type.DiagnosticRefreshRequest,
                execute=self.respond_diagnostic_refresh,
            ),
        )
