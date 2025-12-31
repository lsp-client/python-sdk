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
class WithRequestImplementation(
    TextDocumentCapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `textDocument/implementation` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_implementation
    """

    @override
    @classmethod
    def iter_methods(cls) -> Iterator[str]:
        yield from super().iter_methods()
        yield from (lsp_type.TEXT_DOCUMENT_IMPLEMENTATION,)

    @override
    @classmethod
    def register_text_document_capability(
        cls, cap: lsp_type.TextDocumentClientCapabilities
    ) -> None:
        cap.implementation = lsp_type.ImplementationClientCapabilities(
            link_support=True,
        )

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)
        assert cap.implementation_provider

    async def _request_implementation(
        self, params: lsp_type.ImplementationParams
    ) -> lsp_type.ImplementationResult:
        return await self.request(
            lsp_type.ImplementationRequest(
                id=jsonrpc_uuid(),
                params=params,
            ),
            schema=lsp_type.ImplementationResponse,
        )

    async def request_implementation(
        self, file_path: AnyPath, position: Position
    ) -> (
        lsp_type.Location
        | Sequence[lsp_type.Location]
        | Sequence[lsp_type.LocationLink]
        | None
    ):
        async with self.open_files(file_path):
            return await self._request_implementation(
                lsp_type.ImplementationParams(
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                )
            )

    @deprecated("Prefer using `request_implementation_links` for LocationLink results.")
    async def request_implementation_locations(
        self, file_path: AnyPath, position: Position
    ) -> Sequence[lsp_type.Location] | None:
        match await self.request_implementation(file_path, position):
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
                logger.warning(
                    "Implementation returned with unexpected result: {}", other
                )
                return None

    async def request_implementation_links(
        self, file_path: AnyPath, position: Position
    ) -> Sequence[lsp_type.LocationLink] | None:
        match await self.request_implementation(file_path, position):
            case links if is_location_links(links):
                return list(links)
            case None:
                return None
            case other:
                logger.warning(
                    "Implementation returned with unexpected result: {}", other
                )
                return None
