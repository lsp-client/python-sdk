from __future__ import annotations

from typing import TYPE_CHECKING

from lsp_client.exception import LSPError

if TYPE_CHECKING:
    from .abc import Client


class ClientError(LSPError):
    """Base exception for client-related errors."""


class ClientRuntimeError(ClientError):
    """Raised when a client encounters a runtime error."""

    def __init__(self, client: Client, *args: object) -> None:
        super().__init__(*args)
        self.client = client
