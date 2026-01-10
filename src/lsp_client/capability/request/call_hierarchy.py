from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Protocol, override, runtime_checkable

import asyncer
from lsprotocol.types import TextDocumentClientCapabilities

from lsp_client.jsonrpc.id import jsonrpc_uuid
from lsp_client.protocol import CapabilityClientProtocol, TextDocumentCapabilityProtocol
from lsp_client.utils.types import AnyPath, Position, lsp_type


@runtime_checkable
class WithRequestCallHierarchy(
    TextDocumentCapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `callHierarchy/prepare` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_prepareCallHierarchy
    `callHierarchy/incomingCalls` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#callHierarchy_incomingCalls
    `callHierarchy/outgoingCalls` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#callHierarchy_outgoingCalls
    """

    @override
    @classmethod
    def iter_methods(cls) -> Iterator[str]:
        yield from super().iter_methods()
        yield from (
            lsp_type.TEXT_DOCUMENT_PREPARE_CALL_HIERARCHY,
            lsp_type.CALL_HIERARCHY_INCOMING_CALLS,
            lsp_type.CALL_HIERARCHY_OUTGOING_CALLS,
        )

    @override
    @classmethod
    def register_text_document_capability(
        cls, cap: TextDocumentClientCapabilities
    ) -> None:
        super().register_text_document_capability(cap)
        cap.call_hierarchy = lsp_type.CallHierarchyClientCapabilities()

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)
        assert cap.call_hierarchy_provider

    async def _request_call_hierarchy_prepare(
        self, params: lsp_type.CallHierarchyPrepareParams
    ) -> lsp_type.CallHierarchyPrepareResult:
        return await self.request(
            lsp_type.CallHierarchyPrepareRequest(
                id=jsonrpc_uuid(),
                params=params,
            ),
            schema=lsp_type.CallHierarchyPrepareResponse,
        )

    async def _request_call_hierarchy_incoming_calls(
        self, params: lsp_type.CallHierarchyIncomingCallsParams
    ) -> lsp_type.CallHierarchyIncomingCallsResult:
        return await self.request(
            lsp_type.CallHierarchyIncomingCallsRequest(
                id=jsonrpc_uuid(),
                params=params,
            ),
            schema=lsp_type.CallHierarchyIncomingCallsResponse,
        )

    async def _request_call_hierarchy_outgoing_calls(
        self, params: lsp_type.CallHierarchyOutgoingCallsParams
    ) -> lsp_type.CallHierarchyOutgoingCallsResult:
        return await self.request(
            lsp_type.CallHierarchyOutgoingCallsRequest(
                id=jsonrpc_uuid(),
                params=params,
            ),
            schema=lsp_type.CallHierarchyOutgoingCallsResponse,
        )

    async def prepare_call_hierarchy(
        self, file_path: AnyPath, position: Position
    ) -> Sequence[lsp_type.CallHierarchyItem] | None:
        async with self.open_files(file_path):
            return await self._request_call_hierarchy_prepare(
                lsp_type.CallHierarchyPrepareParams(
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                )
            )

    async def request_call_hierarchy_incoming_call(
        self, file_path: AnyPath, position: Position
    ) -> list[lsp_type.CallHierarchyIncomingCall] | None:
        """
        Note: For symbol with multiple definitions, this method will return a list of
        all incoming calls for each definition.
        """

        async with self.open_files(file_path):
            prepared = await self._request_call_hierarchy_prepare(
                lsp_type.CallHierarchyPrepareParams(
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                )
            )

            if not prepared:
                return None

            calls: list[lsp_type.CallHierarchyIncomingCall] = []

            async def request(item: lsp_type.CallHierarchyItem) -> None:
                if resp := await self._request_call_hierarchy_incoming_calls(
                    lsp_type.CallHierarchyIncomingCallsParams(item=item)
                ):
                    calls.extend(resp)

            async with asyncer.create_task_group() as tg:
                for item in prepared:
                    tg.soonify(request)(item)

            if calls:
                return calls
        return None

    async def request_call_hierarchy_outgoing_call(
        self, file_path: AnyPath, position: Position
    ) -> list[lsp_type.CallHierarchyOutgoingCall] | None:
        """
        Note: For symbol with multiple definitions, this method will return a list of
        all outgoing calls for each definition.
        """

        async with self.open_files(file_path):
            prepared = await self._request_call_hierarchy_prepare(
                lsp_type.CallHierarchyPrepareParams(
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    position=position,
                )
            )

            if not prepared:
                return None

            calls: list[lsp_type.CallHierarchyOutgoingCall] = []

            async def append_calls(item: lsp_type.CallHierarchyItem) -> None:
                if resp := await self._request_call_hierarchy_outgoing_calls(
                    lsp_type.CallHierarchyOutgoingCallsParams(item=item)
                ):
                    calls.extend(resp)

            async with asyncer.create_task_group() as tg:
                for item in prepared:
                    tg.soonify(append_calls)(item)

            if calls:
                return calls
        return None
