from __future__ import annotations

from typing import TYPE_CHECKING

from lsp_client.exception import LSPError

if TYPE_CHECKING:
    from .abc import Server


class ServerError(LSPError):
    """Base exception for server-related errors."""


class ServerRuntimeError(ServerError):
    """Raised when a server fails to start or crashes during execution."""

    def __init__(self, server: Server, *args: object) -> None:
        super().__init__(*args)
        self.server = server


class ServerInstallationError(ServerError):
    """Raised when a server executable cannot be found or installed."""
