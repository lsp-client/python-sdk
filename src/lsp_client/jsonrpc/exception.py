from __future__ import annotations

from lsp_client.exception import LSPError


class JsonRpcError(LSPError):
    """Base exception for JSON-RPC related errors."""


class JsonRpcParseError(JsonRpcError):
    """Raised when parsing a JSON-RPC message fails."""


class JsonRpcTransportError(JsonRpcError):
    """Raised when the transport connection fails (e.g. unexpected EOF)."""


class JsonRpcResponseError(JsonRpcError):
    """Raised when the JSON-RPC response indicates an error."""

    def __init__(self, code: int, message: str, data: object = None) -> None:
        super().__init__(f"JSON-RPC Error {code}: {message}")
        self.code = code
        self.message = message
        self.data = data
