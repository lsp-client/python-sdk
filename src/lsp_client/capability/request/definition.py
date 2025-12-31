from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Protocol, override, runtime_checkable

from loguru import logger

from lsp_client.jsonrpc.id import jsonrpc_uuid
from lsp_client.protocol import (
    CapabilityClientProtocol,
    TextDocumentCapabilityProtocol,
)
from lsp_client.utils.type_guard import is_location_links, is_locations
from lsp_client.utils.types import AnyPath, Position, lsp_type
from lsp_client.utils.warn import deprecated


@runtime_checkable
class WithRequestDefinition(
    TextDocumentCapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `textDocument/definition` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_definition
    """

    @override
    @classmethod
    def iter_methods(cls) -> Iterator[str]:
        yield from super().iter_methods()
        yield from (lsp_type.TEXT_DOCUMENT_DEFINITION,)

    @override
    @classmethod
    def register_text_document_capability(
        cls, cap: lsp_type.TextDocumentClientCapabilities
    ) -> None:
        cap.definition = lsp_type.DefinitionClientCapabilities(
            link_support=True,
        )

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)
        assert cap.definition_provider

    async def _request_definition(
        self, params: lsp_type.DefinitionParams
    ) -> lsp_type.DefinitionResult:
        return await self.request(
            lsp_type.DefinitionRequest(
                id=jsonrpc_uuid(),
                params=params,
            ),
            schema=lsp_type.DefinitionResponse,
        )

    async def request_definition(
        self,
        file_path: AnyPath,
        position: Position,
    ) -> (
        lsp_type.Location
        | Sequence[lsp_type.Location]
        | Sequence[lsp_type.LocationLink]
        | None
    ):
        async with self.open_files(file_path):
            return await self._request_definition(
                lsp_type.DefinitionParams(
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                )
            )

    @deprecated("Prefer using 'request_definition_links' for LocationLink results.")
    async def request_definition_locations(
        self,
        file_path: AnyPath,
        position: Position,
    ) -> Sequence[lsp_type.Location] | None:
        match await self.request_definition(file_path, position):
            case lsp_type.Location() as loc:
                return [loc]
            case locations if is_locations(locations):
                return list(locations)
            case links if is_location_links(links):
                return [
                    lsp_type.Location(
                        uri=link.target_uri,
                        range=link.target_selection_range,
                    )
                    for link in links
                ]
            case None:
                return None
            case other:
                logger.warning("Definition returned with unexpected result: {}", other)
                return None

    async def request_definition_links(
        self,
        file_path: AnyPath,
        position: Position,
    ) -> Sequence[lsp_type.LocationLink] | None:
        match await self.request_definition(file_path, position):
            case links if is_location_links(links):
                return list(links)
            case None:
                return None
            case other:
                logger.warning("Definition returned with unexpected result: {}", other)
                return None
