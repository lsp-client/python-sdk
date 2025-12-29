from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Protocol, override, runtime_checkable

import asyncer

from lsp_client.jsonrpc.id import jsonrpc_uuid
from lsp_client.protocol import CapabilityClientProtocol, TextDocumentCapabilityProtocol
from lsp_client.utils.types import AnyPath, Range, lsp_type


@runtime_checkable
class WithRequestInlayHint(
    TextDocumentCapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `textDocument/inlayHint` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_inlayHint
    """

    @override
    @classmethod
    def iter_methods(cls) -> Iterator[str]:
        yield from super().iter_methods()
        yield from (
            lsp_type.TEXT_DOCUMENT_INLAY_HINT,
            lsp_type.INLAY_HINT_RESOLVE,
        )

    @override
    @classmethod
    def register_text_document_capability(
        cls, cap: lsp_type.TextDocumentClientCapabilities
    ) -> None:
        cap.inlay_hint = lsp_type.InlayHintClientCapabilities(
            resolve_support=lsp_type.ClientInlayHintResolveOptions(
                properties=[
                    "tooltip",
                    "location",
                    "label.tooltip",
                    "label.location",
                    "textEdits",
                ]
            ),
        )

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)
        assert cap.inlay_hint_provider

    def get_inlay_hint_label(
        self, hint: lsp_type.InlayHint | lsp_type.InlayHintLabelPart
    ) -> str:
        """Extract the text label from an InlayHint or InlayHintLabelPart."""
        match hint:
            case lsp_type.InlayHintLabelPart(value=value):
                return value
            case lsp_type.InlayHint(label=str() as label):
                return label
            case lsp_type.InlayHint(label=parts):
                return "".join(part.value for part in parts)
            case _:
                raise TypeError(f"Unexpected type for inlay hint label: {type(hint)}")

    async def _request_inlay_hint(
        self, params: lsp_type.InlayHintParams
    ) -> lsp_type.InlayHintResult:
        return await self.request(
            lsp_type.InlayHintRequest(
                id=jsonrpc_uuid(),
                params=params,
            ),
            schema=lsp_type.InlayHintResponse,
        )

    async def _request_inlay_hint_resolve(
        self, params: lsp_type.InlayHint
    ) -> lsp_type.InlayHint:
        return await self.request(
            lsp_type.InlayHintResolveRequest(
                id=jsonrpc_uuid(),
                params=params,
            ),
            schema=lsp_type.InlayHintResolveResponse,
        )

    async def request_inlay_hint(
        self,
        file_path: AnyPath,
        range: Range,
        *,
        resolve: bool = False,
    ) -> Sequence[lsp_type.InlayHint] | None:
        """
        Request inlay hints for a given file and range.

        This sends a `textDocument/inlayHint` request for the specified document range.
        If ``resolve`` is True, each returned inlay hint is further resolved using
        :meth:`request_inlay_hint_resolve` to populate optional properties such as
        tooltip, locations, and text edits.

        :param file_path: Path to the file for which inlay hints are requested.
        :param range: LSP range within the document to compute inlay hints for.
        :param resolve: Whether to resolve each returned inlay hint for additional
            details supported by the server.
        :return: A sequence of :class:`lsp_type.InlayHint` instances if the server
            returns hints, or ``None`` if no hints are provided.
        """
        async with self.open_files(file_path):
            hints = await self._request_inlay_hint(
                lsp_type.InlayHintParams(
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    range=range,
                )
            )

        if resolve and hints:
            async with asyncer.create_task_group() as tg:
                tasks = [
                    tg.soonify(self.request_inlay_hint_resolve)(hint) for hint in hints
                ]
            return [task.value for task in tasks]

        return hints

    async def request_inlay_hint_resolve(
        self, hint: lsp_type.InlayHint
    ) -> lsp_type.InlayHint:
        """
        Resolve additional details for a previously returned inlay hint.

        This sends an LSP ``inlayHint/resolve`` request to the server for the
        given ``hint``. Servers may initially return inlay hints with only a
        subset of properties populated and require a subsequent resolve
        request to fill in optional fields such as tooltips, locations, or
        text edits.

        :param hint: An :class:`lsp_type.InlayHint` instance obtained from a
            prior ``textDocument/inlayHint`` request that should be fully
            resolved by the server.
        :return: A new :class:`lsp_type.InlayHint` containing any additional
            data supplied by the server.
        """
        return await self._request_inlay_hint_resolve(hint)
