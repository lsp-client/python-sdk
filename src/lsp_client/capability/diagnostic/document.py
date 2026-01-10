from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Protocol, override, runtime_checkable

from loguru import logger

from lsp_client.jsonrpc.id import jsonrpc_uuid
from lsp_client.protocol import CapabilityClientProtocol, TextDocumentCapabilityProtocol
from lsp_client.utils.types import AnyPath, lsp_type


@runtime_checkable
class WithDocumentDiagnostic(
    TextDocumentCapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `textDocument/diagnostic` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_pullDiagnostics
    """

    @override
    @classmethod
    def iter_methods(cls) -> Iterator[str]:
        yield from super().iter_methods()
        yield lsp_type.TEXT_DOCUMENT_DIAGNOSTIC

    @override
    @classmethod
    def register_text_document_capability(
        cls, cap: lsp_type.TextDocumentClientCapabilities
    ) -> None:
        super().register_text_document_capability(cap)
        cap.diagnostic = lsp_type.DiagnosticClientCapabilities(
            related_document_support=True,
            related_information=True,
            tag_support=lsp_type.ClientDiagnosticsTagOptions(
                value_set=[*lsp_type.DiagnosticTag]
            ),
            code_description_support=True,
            data_support=True,
        )

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)
        assert cap.diagnostic_provider

    async def _request_diagnostic(
        self, params: lsp_type.DocumentDiagnosticParams
    ) -> lsp_type.DocumentDiagnosticReport:
        return await self.request(
            lsp_type.DocumentDiagnosticRequest(
                id=jsonrpc_uuid(),
                params=params,
            ),
            schema=lsp_type.DocumentDiagnosticResponse,
        )

    async def request_diagnostic(
        self,
        file_path: AnyPath,
        *,
        identifier: str | None = None,
        previous_result_id: str | None = None,
    ) -> lsp_type.DocumentDiagnosticReport | None:
        """
        `textDocument/diagnostic` - Request a diagnostic report for a document.
        """

        async with self.open_files(file_path):
            return await self._request_diagnostic(
                lsp_type.DocumentDiagnosticParams(
                    text_document=lsp_type.TextDocumentIdentifier(
                        uri=self.as_uri(file_path)
                    ),
                    identifier=identifier,
                    previous_result_id=previous_result_id,
                )
            )

    async def request_diagnostics(
        self,
        file_path: AnyPath,
        *,
        identifier: str | None = None,
        previous_result_id: str | None = None,
    ) -> Sequence[lsp_type.Diagnostic] | None:
        """
        Request diagnostics for a document. Returns only the list of diagnostics.
        """
        match await self.request_diagnostic(
            file_path,
            identifier=identifier,
            previous_result_id=previous_result_id,
        ):
            case (
                lsp_type.RelatedFullDocumentDiagnosticReport(items=items)
                | lsp_type.RelatedUnchangedDocumentDiagnosticReport(items=items)
            ):
                return items
            case _:
                logger.warning(
                    "Unsupported diagnostic report type for file {}",
                    file_path,
                )
        return None
