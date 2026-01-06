from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Protocol, override, runtime_checkable

from lsp_client.protocol import CapabilityClientProtocol, TextDocumentCapabilityProtocol
from lsp_client.utils.types import AnyPath, lsp_type


@runtime_checkable
class WithNotifyTextDocumentSynchronize(
    TextDocumentCapabilityProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `textDocument/didOpen` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_didOpen
    `textDocument/didChange` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_didChange
    `textDocument/didClose` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_didClose
    """

    @override
    @classmethod
    def iter_methods(cls) -> Iterator[str]:
        yield from super().iter_methods()
        yield from (
            lsp_type.TEXT_DOCUMENT_DID_OPEN,
            lsp_type.TEXT_DOCUMENT_DID_CHANGE,
            lsp_type.TEXT_DOCUMENT_DID_CLOSE,
        )

    @override
    @classmethod
    def register_text_document_capability(
        cls, cap: lsp_type.TextDocumentClientCapabilities
    ) -> None:
        super().register_text_document_capability(cap)
        cap.synchronization = lsp_type.TextDocumentSyncClientCapabilities(
            will_save=True,
            will_save_wait_until=True,
            did_save=True,
        )

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)
        assert cap.text_document_sync

    async def _notify_text_document_opened(
        self, params: lsp_type.DidOpenTextDocumentParams
    ) -> None:
        return await self.notify(
            lsp_type.DidOpenTextDocumentNotification(params=params)
        )

    async def notify_text_document_opened(
        self, file_path: AnyPath, file_content: str
    ) -> None:
        uri = self.as_uri(file_path)
        return await self._notify_text_document_opened(
            lsp_type.DidOpenTextDocumentParams(
                text_document=lsp_type.TextDocumentItem(
                    uri=uri,
                    language_id=self.get_language_config().kind,
                    version=0,
                    text=file_content,
                )
            )
        )

    async def _notify_text_document_changed(
        self, params: lsp_type.DidChangeTextDocumentParams
    ) -> None:
        return await self.notify(
            lsp_type.DidChangeTextDocumentNotification(params=params)
        )

    async def notify_text_document_changed(
        self,
        file_path: AnyPath,
        content_changes: Sequence[lsp_type.TextDocumentContentChangeEvent],
        version: int = 0,
    ) -> None:
        return await self._notify_text_document_changed(
            lsp_type.DidChangeTextDocumentParams(
                text_document=lsp_type.VersionedTextDocumentIdentifier(
                    uri=self.as_uri(file_path), version=version
                ),
                content_changes=list(content_changes),
            )
        )

    async def _notify_text_document_closed(
        self, params: lsp_type.DidCloseTextDocumentParams
    ) -> None:
        return await self.notify(
            lsp_type.DidCloseTextDocumentNotification(params=params)
        )

    async def notify_text_document_closed(self, file_path: AnyPath) -> None:
        return await self._notify_text_document_closed(
            lsp_type.DidCloseTextDocumentParams(
                text_document=lsp_type.TextDocumentIdentifier(
                    uri=self.as_uri(file_path)
                ),
            )
        )
