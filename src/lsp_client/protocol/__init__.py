"""LSP protocol abstractions and type definitions.

This module defines the protocol interfaces for LSP client capabilities,
server request/notification hooks, and client operations.
"""

from __future__ import annotations

from .capability import (
    CapabilityProtocol,
    ExperimentalCapabilityProtocol,
    GeneralCapabilityProtocol,
    NotebookCapabilityProtocol,
    TextDocumentCapabilityProtocol,
    WindowCapabilityProtocol,
    WorkspaceCapabilityProtocol,
)
from .client import CapabilityClientProtocol
from .hook import (
    ServerNotificationHook,
    ServerNotificationHookExecutor,
    ServerRequestHook,
    ServerRequestHookExecutor,
    ServerRequestHookProtocol,
    ServerRequestHookRegistry,
)

__all__ = [
    "CapabilityClientProtocol",
    "CapabilityProtocol",
    "ExperimentalCapabilityProtocol",
    "GeneralCapabilityProtocol",
    "NotebookCapabilityProtocol",
    "ServerNotificationHook",
    "ServerNotificationHookExecutor",
    "ServerRequestHook",
    "ServerRequestHookExecutor",
    "ServerRequestHookProtocol",
    "ServerRequestHookRegistry",
    "TextDocumentCapabilityProtocol",
    "WindowCapabilityProtocol",
    "WorkspaceCapabilityProtocol",
]
