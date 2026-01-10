from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Protocol, override, runtime_checkable

import asyncer

from lsp_client.jsonrpc.id import jsonrpc_uuid
from lsp_client.protocol import CapabilityClientProtocol, TextDocumentCapabilityProtocol
from lsp_client.utils.types import AnyPath, Position, lsp_type


@runtime_checkable
class WithRequestTypeHierarchy(
    TextDocumentCapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `textDocument/prepareTypeHierarchy` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_prepareTypeHierarchy
    """

    @override
    @classmethod
    def iter_methods(cls) -> Iterator[str]:
        yield from super().iter_methods()
        yield from (
            lsp_type.TEXT_DOCUMENT_PREPARE_TYPE_HIERARCHY,
            lsp_type.TYPE_HIERARCHY_SUPERTYPES,
            lsp_type.TYPE_HIERARCHY_SUBTYPES,
        )

    @override
    @classmethod
    def register_text_document_capability(
        cls, cap: lsp_type.TextDocumentClientCapabilities
    ) -> None:
        super().register_text_document_capability(cap)
        cap.type_hierarchy = lsp_type.TypeHierarchyClientCapabilities()

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)
        assert cap.type_hierarchy_provider

    async def _request_type_hierarchy_prepare(
        self, params: lsp_type.TypeHierarchyPrepareParams
    ) -> lsp_type.TypeHierarchyPrepareResult:
        return await self.request(
            lsp_type.TypeHierarchyPrepareRequest(
                id=jsonrpc_uuid(),
                params=params,
            ),
            schema=lsp_type.TypeHierarchyPrepareResponse,
        )

    async def _request_type_hierarchy_supertypes(
        self, params: lsp_type.TypeHierarchySupertypesParams
    ) -> lsp_type.TypeHierarchySupertypesResult:
        return await self.request(
            lsp_type.TypeHierarchySupertypesRequest(
                id=jsonrpc_uuid(),
                params=params,
            ),
            schema=lsp_type.TypeHierarchySupertypesResponse,
        )

    async def _request_type_hierarchy_subtypes(
        self, params: lsp_type.TypeHierarchySubtypesParams
    ) -> lsp_type.TypeHierarchySubtypesResult:
        return await self.request(
            lsp_type.TypeHierarchySubtypesRequest(
                id=jsonrpc_uuid(),
                params=params,
            ),
            schema=lsp_type.TypeHierarchySubtypesResponse,
        )

    async def prepare_type_hierarchy(
        self, file_path: AnyPath, position: Position
    ) -> Sequence[lsp_type.TypeHierarchyItem] | None:
        async with self.open_files(file_path):
            return await self._request_type_hierarchy_prepare(
                lsp_type.TypeHierarchyPrepareParams(
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                )
            )

    async def request_type_hierarchy_supertypes(
        self, file_path: AnyPath, position: Position
    ) -> list[lsp_type.TypeHierarchyItem] | None:
        async with self.open_files(file_path):
            prepared = await self._request_type_hierarchy_prepare(
                lsp_type.TypeHierarchyPrepareParams(
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                )
            )

            if not prepared:
                return None

            items: list[lsp_type.TypeHierarchyItem] = []

            async def append_items(item: lsp_type.TypeHierarchyItem) -> None:
                if resp := await self._request_type_hierarchy_supertypes(
                    lsp_type.TypeHierarchySupertypesParams(item=item)
                ):
                    items.extend(resp)

            async with asyncer.create_task_group() as tg:
                for item in prepared:
                    tg.soonify(append_items)(item)

            if items:
                return items
        return None

    async def request_type_hierarchy_subtypes(
        self, file_path: AnyPath, position: Position
    ) -> list[lsp_type.TypeHierarchyItem] | None:
        async with self.open_files(file_path):
            prepared = await self._request_type_hierarchy_prepare(
                lsp_type.TypeHierarchyPrepareParams(
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                )
            )

            if not prepared:
                return None

            items: list[lsp_type.TypeHierarchyItem] = []

            async def append_items(item: lsp_type.TypeHierarchyItem) -> None:
                if resp := await self._request_type_hierarchy_subtypes(
                    lsp_type.TypeHierarchySubtypesParams(item=item)
                ):
                    items.extend(resp)

            async with asyncer.create_task_group() as tg:
                for item in prepared:
                    tg.soonify(append_items)(item)

            if items:
                return items
        return None
