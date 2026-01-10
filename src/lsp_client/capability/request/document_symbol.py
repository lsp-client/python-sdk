from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Protocol, override, runtime_checkable

from loguru import logger

from lsp_client.jsonrpc.id import jsonrpc_uuid
from lsp_client.protocol import CapabilityClientProtocol, TextDocumentCapabilityProtocol
from lsp_client.utils.type_guard import is_document_symbols, is_symbol_information_seq
from lsp_client.utils.types import AnyPath, lsp_type
from lsp_client.utils.warn import deprecated


@runtime_checkable
class WithRequestDocumentSymbol(
    TextDocumentCapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `text_document/document_symbol` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_documentSymbol
    """

    @override
    @classmethod
    def iter_methods(cls) -> Iterator[str]:
        yield from super().iter_methods()
        yield from (lsp_type.TEXT_DOCUMENT_DOCUMENT_SYMBOL,)

    @override
    @classmethod
    def register_text_document_capability(
        cls, cap: lsp_type.TextDocumentClientCapabilities
    ) -> None:
        super().register_text_document_capability(cap)
        cap.document_symbol = lsp_type.DocumentSymbolClientCapabilities(
            symbol_kind=lsp_type.ClientSymbolKindOptions(
                value_set=[*lsp_type.SymbolKind]
            ),
            hierarchical_document_symbol_support=True,
            tag_support=lsp_type.ClientSymbolTagOptions(
                value_set=[*lsp_type.SymbolTag],
            ),
            label_support=True,
        )

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)
        assert cap.document_symbol_provider

    async def _request_document_symbol(
        self, params: lsp_type.DocumentSymbolParams
    ) -> lsp_type.DocumentSymbolResult | None:
        return await self.request(
            lsp_type.DocumentSymbolRequest(
                id=jsonrpc_uuid(),
                params=params,
            ),
            schema=lsp_type.DocumentSymbolResponse,
        )

    async def request_document_symbol(
        self, file_path: AnyPath
    ) -> (
        Sequence[lsp_type.SymbolInformation] | Sequence[lsp_type.DocumentSymbol] | None
    ):
        async with self.open_files(file_path):
            return await self._request_document_symbol(
                lsp_type.DocumentSymbolParams(
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path),
                    ),
                ),
            )

    @deprecated(
        "Use 'request_document_symbol_information_list' or "
        "'request_document_symbol_list' instead."
    )
    async def request_document_symbol_information_list(
        self, file_path: AnyPath
    ) -> Sequence[lsp_type.SymbolInformation] | None:
        match await self.request_document_symbol(file_path):
            case result if is_symbol_information_seq(result):
                return list(result)
            case other:
                logger.warning(
                    "Document symbol returned with unexpected result: {}", other
                )
        return None

    async def request_document_symbol_list(
        self, file_path: AnyPath
    ) -> Sequence[lsp_type.DocumentSymbol] | None:
        match await self.request_document_symbol(file_path):
            case result if is_document_symbols(result):
                return list(result)
            case other:
                logger.warning(
                    "Document symbol returned with unexpected result: {}", other
                )
                return None
