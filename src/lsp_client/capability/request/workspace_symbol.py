from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Protocol, override, runtime_checkable

import asyncer
from loguru import logger

from lsp_client.jsonrpc.id import jsonrpc_uuid
from lsp_client.protocol import CapabilityClientProtocol, WorkspaceCapabilityProtocol
from lsp_client.utils.type_guard import is_symbol_information_seq, is_workspace_symbols
from lsp_client.utils.types import lsp_type
from lsp_client.utils.warn import deprecated


@runtime_checkable
class WithRequestWorkspaceSymbol(
    WorkspaceCapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    - `workspace/symbol` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_symbol
    - `workspace/symbolResolve` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_symbolResolve
    """

    @override
    @classmethod
    def iter_methods(cls) -> Iterator[str]:
        yield from super().iter_methods()
        yield from (
            lsp_type.WORKSPACE_SYMBOL,
            lsp_type.WORKSPACE_SYMBOL_RESOLVE,
        )

    @override
    @classmethod
    def register_workspace_capability(
        cls, cap: lsp_type.WorkspaceClientCapabilities
    ) -> None:
        super().register_workspace_capability(cap)
        cap.symbol = lsp_type.WorkspaceSymbolClientCapabilities(
            symbol_kind=lsp_type.ClientSymbolKindOptions(
                value_set=[*lsp_type.SymbolKind]
            ),
            tag_support=lsp_type.ClientSymbolTagOptions(
                value_set=[*lsp_type.SymbolTag],
            ),
            resolve_support=lsp_type.ClientSymbolResolveOptions(
                properties=["location.range", "location.uri"]
            ),
        )

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)
        assert cap.workspace_symbol_provider

    async def _request_workspace_symbol(
        self, params: lsp_type.WorkspaceSymbolParams
    ) -> lsp_type.WorkspaceSymbolResult:
        return await self.request(
            lsp_type.WorkspaceSymbolRequest(
                id=jsonrpc_uuid(),
                params=params,
            ),
            schema=lsp_type.WorkspaceSymbolResponse,
        )

    async def request_workspace_symbol(
        self, query: str
    ) -> (
        Sequence[lsp_type.SymbolInformation] | Sequence[lsp_type.WorkspaceSymbol] | None
    ):
        return await self._request_workspace_symbol(
            lsp_type.WorkspaceSymbolParams(query=query)
        )

    async def _request_workspace_symbol_resolve(
        self, params: lsp_type.WorkspaceSymbol
    ) -> lsp_type.WorkspaceSymbol:
        return await self.request(
            lsp_type.WorkspaceSymbolResolveRequest(
                id=jsonrpc_uuid(),
                params=params,
            ),
            schema=lsp_type.WorkspaceSymbolResolveResponse,
        )

    async def request_workspace_symbol_resolve(
        self, symbol: lsp_type.WorkspaceSymbol
    ) -> lsp_type.WorkspaceSymbol:
        return await self._request_workspace_symbol_resolve(symbol)

    async def resolve_workspace_symbols(
        self,
        symbols: Sequence[lsp_type.WorkspaceSymbol],
    ) -> Sequence[lsp_type.WorkspaceSymbol]:
        tasks: list[asyncer.SoonValue[lsp_type.WorkspaceSymbol]] = []
        async with asyncer.create_task_group() as tg:
            tasks = [
                tg.soonify(self.request_workspace_symbol_resolve)(symbol)
                for symbol in symbols
            ]
        return [task.value for task in tasks]

    @deprecated("Use 'request_workspace_symbol_list' instead.")
    async def request_workspace_symbol_information_list(
        self, query: str
    ) -> Sequence[lsp_type.SymbolInformation]:
        """
        Request workspace symbols as a list of SymbolInformation.
        Returns an empty list if the server returns WorkspaceSymbol or null.
        """
        match await self.request_workspace_symbol(query):
            case result if is_symbol_information_seq(result):
                return list(result)
            case other:
                if other is not None:
                    logger.warning(
                        "Workspace symbol returned with unexpected result: {}", other
                    )
                return []

    async def request_workspace_symbol_list(
        self, query: str, *, resolve: bool = False
    ) -> Sequence[lsp_type.WorkspaceSymbol]:
        """
        Request workspace symbols as a list of WorkspaceSymbol.
        Automatically converts SymbolInformation to WorkspaceSymbol if needed.
        Returns an empty list if no results are found.
        """
        match await self.request_workspace_symbol(query):
            case result if is_workspace_symbols(result):
                res = list(result)
                if resolve:
                    return await self.resolve_workspace_symbols(res)
                return res
            case result if is_symbol_information_seq(result):
                return [
                    lsp_type.WorkspaceSymbol(
                        name=s.name,
                        kind=s.kind,
                        tags=list(s.tags)
                        if s.tags
                        else (
                            [lsp_type.SymbolTag.Deprecated] if s.deprecated else None
                        ),
                        container_name=s.container_name,
                        location=s.location,
                    )
                    for s in result
                ]
            case other:
                if other is not None:
                    logger.warning(
                        "Workspace symbol returned with unexpected result: {}", other
                    )
                return []
