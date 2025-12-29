from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Protocol, override, runtime_checkable

from lsp_client.jsonrpc.id import jsonrpc_uuid
from lsp_client.protocol import CapabilityClientProtocol, TextDocumentCapabilityProtocol
from lsp_client.utils.types import AnyPath, Range, lsp_type


@runtime_checkable
class WithRequestInlineValue(
    TextDocumentCapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `textDocument/inlineValue` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_inlineValue
    """

    @override
    @classmethod
    def iter_methods(cls) -> Iterator[str]:
        yield from super().iter_methods()
        yield from (lsp_type.TEXT_DOCUMENT_INLINE_VALUE,)

    @override
    @classmethod
    def register_text_document_capability(
        cls, cap: lsp_type.TextDocumentClientCapabilities
    ) -> None:
        cap.inline_value = lsp_type.InlineValueClientCapabilities()

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)
        assert cap.inline_value_provider

    async def _request_inline_value(
        self, params: lsp_type.InlineValueParams
    ) -> lsp_type.InlineValueResult:
        return await self.request(
            lsp_type.InlineValueRequest(
                id=jsonrpc_uuid(),
                params=params,
            ),
            schema=lsp_type.InlineValueResponse,
        )

    async def request_inline_value(
        self,
        file_path: AnyPath,
        range: Range,
        context: lsp_type.InlineValueContext,
    ) -> Sequence[lsp_type.InlineValue] | None:
        """
        Request inline values for the given range in the text document.

        Args:
            file_path: Path to the text document
            range: Range for which inline values are requested
            context: Debug session context information

        Returns:
            List of inline value objects containing the computed inline values
        """
        async with self.open_files(file_path):
            return await self._request_inline_value(
                lsp_type.InlineValueParams(
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    range=range,
                    context=context,
                )
            )
