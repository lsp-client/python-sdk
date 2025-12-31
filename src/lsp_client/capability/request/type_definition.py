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
class WithRequestTypeDefinition(
    TextDocumentCapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `textDocument/typeDefinition` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_typeDefinition
    """

    @override
    @classmethod
    def iter_methods(cls) -> Iterator[str]:
        yield from super().iter_methods()
        yield from (lsp_type.TEXT_DOCUMENT_TYPE_DEFINITION,)

    @override
    @classmethod
    def register_text_document_capability(
        cls, cap: lsp_type.TextDocumentClientCapabilities
    ) -> None:
        cap.type_definition = lsp_type.TypeDefinitionClientCapabilities(
            link_support=True,
        )

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)
        assert cap.type_definition_provider

    async def _request_type_definition(
        self, params: lsp_type.TypeDefinitionParams
    ) -> lsp_type.TypeDefinitionResult:
        return await self.request(
            lsp_type.TypeDefinitionRequest(
                id=jsonrpc_uuid(),
                params=params,
            ),
            schema=lsp_type.TypeDefinitionResponse,
        )

    async def request_type_definition(
        self, file_path: AnyPath, position: Position
    ) -> (
        lsp_type.Location
        | Sequence[lsp_type.Location]
        | Sequence[lsp_type.LocationLink]
        | None
    ):
        async with self.open_files(file_path):
            return await self._request_type_definition(
                lsp_type.TypeDefinitionParams(
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                )
            )

    @deprecated(
        "Prefer using 'request_type_definition_links' for LocationLink support."
    )
    async def request_type_definition_locations(
        self, file_path: AnyPath, position: Position
    ) -> Sequence[lsp_type.Location] | None:
        match await self.request_type_definition(file_path, position):
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
                    "TypeDefinition returned with unexpected result: {}", other
                )
                return None

    async def request_type_definition_links(
        self, file_path: AnyPath, position: Position
    ) -> Sequence[lsp_type.LocationLink] | None:
        match await self.request_type_definition(file_path, position):
            case links if is_location_links(links):
                return list(links)
            case None:
                return None
            case other:
                logger.warning(
                    "TypeDefinition returned with unexpected result: {}", other
                )
                return None
