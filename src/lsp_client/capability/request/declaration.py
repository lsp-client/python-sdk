from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Protocol, override, runtime_checkable

from loguru import logger

from lsp_client.jsonrpc.id import jsonrpc_uuid
from lsp_client.protocol import CapabilityClientProtocol, TextDocumentCapabilityProtocol
from lsp_client.utils.type_guard import is_location_links, is_locations
from lsp_client.utils.types import AnyPath, Position, lsp_type
from lsp_client.utils.warn import deprecated


@runtime_checkable
class WithRequestDeclaration(
    TextDocumentCapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `textDocument/declaration` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_declaration
    """

    @override
    @classmethod
    def iter_methods(cls) -> Iterator[str]:
        yield from super().iter_methods()
        yield from (lsp_type.TEXT_DOCUMENT_DECLARATION,)

    @override
    @classmethod
    def register_text_document_capability(
        cls, cap: lsp_type.TextDocumentClientCapabilities
    ) -> None:
        cap.declaration = lsp_type.DeclarationClientCapabilities(
            link_support=True,
        )

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)
        assert cap.declaration_provider

    async def _request_declaration(
        self, params: lsp_type.DeclarationParams
    ) -> lsp_type.DeclarationResult:
        return await self.request(
            lsp_type.DeclarationRequest(
                id=jsonrpc_uuid(),
                params=params,
            ),
            schema=lsp_type.DeclarationResponse,
        )

    async def request_declaration(
        self, file_path: AnyPath, position: Position
    ) -> (
        lsp_type.Location
        | Sequence[lsp_type.Location]
        | Sequence[lsp_type.LocationLink]
        | None
    ):
        async with self.open_files(file_path):
            return await self._request_declaration(
                lsp_type.DeclarationParams(
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                )
            )

    @deprecated("Prefer using 'request_declaration_links' for LocationLink results.")
    async def request_declaration_locations(
        self, file_path: AnyPath, position: Position
    ) -> Sequence[lsp_type.Location] | None:
        match await self.request_declaration(file_path, position):
            case lsp_type.Location() as loc:
                return [loc]
            case locations if is_locations(locations):
                return list(locations)
            case links if is_location_links(links):
                return [
                    lsp_type.Location(
                        uri=link.target_uri, range=link.target_selection_range
                    )
                    for link in links
                ]
            case None:
                return None
            case other:
                logger.warning("Declaration returned with unexpected result: {}", other)
                return None

    async def request_declaration_links(
        self, file_path: AnyPath, position: Position
    ) -> Sequence[lsp_type.LocationLink] | None:
        match await self.request_declaration(file_path, position):
            case links if is_location_links(links):
                return list(links)
            case None:
                return None
            case other:
                logger.warning("Declaration returned with unexpected result: {}", other)
                return None
