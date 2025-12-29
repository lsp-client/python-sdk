"""LSP capability protocols defining client-side capability registration.

Provides protocol interfaces for different LSP capability categories:
workspace, text document, notebook, window, general, and experimental capabilities.
Each protocol defines methods for registering client capabilities with the server.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterator
from typing import Any, Protocol, runtime_checkable

from lsp_client.utils.types import lsp_type


@runtime_checkable
class CapabilityProtocol(Protocol):
    """
    Protocol for LSP capability.
    """

    @classmethod
    @abstractmethod
    def iter_methods(cls) -> Iterator[str]:
        """
        LSP methods associated with this capability.
        """

        yield from ()

    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        """
        Check if the server supports current capability.

        When the server does not support the capability, an `AssertionError` should be raised.

        Note: This method is for debugging purposes.
        """

        return


@runtime_checkable
class WorkspaceCapabilityProtocol(
    CapabilityProtocol,
    Protocol,
):
    """
    LSP `workspace` capability.
    """

    @classmethod
    def register_workspace_capability(
        cls, cap: lsp_type.WorkspaceClientCapabilities
    ) -> None:
        return


@runtime_checkable
class TextDocumentCapabilityProtocol(
    CapabilityProtocol,
    Protocol,
):
    """
    LSP `text_document` capability.
    """

    @classmethod
    def register_text_document_capability(
        cls, cap: lsp_type.TextDocumentClientCapabilities
    ) -> None:
        return


@runtime_checkable
class NotebookCapabilityProtocol(
    CapabilityProtocol,
    Protocol,
):
    """
    LSP `notebook_document` capability.
    """

    @classmethod
    def register_notebook_document_capability(
        cls, cap: lsp_type.NotebookDocumentClientCapabilities
    ) -> None:
        return


@runtime_checkable
class WindowCapabilityProtocol(
    CapabilityProtocol,
    Protocol,
):
    """
    LSP `window` capability.
    """

    @classmethod
    def register_window_capability(cls, cap: lsp_type.WindowClientCapabilities) -> None:
        return


@runtime_checkable
class GeneralCapabilityProtocol(
    CapabilityProtocol,
    Protocol,
):
    """
    LSP `general` capability.
    """

    @classmethod
    def register_general_capability(
        cls, cap: lsp_type.GeneralClientCapabilities
    ) -> None:
        return


@runtime_checkable
class ExperimentalCapabilityProtocol(
    CapabilityProtocol,
    Protocol,
):
    """
    LSP `experimental` capability.
    """

    @classmethod
    def register_experimental_capability(cls, cap: dict[str, Any]) -> None:
        return
