"""Server request and notification hook system for LSP client.

Defines hooks for handling server-initiated requests and notifications,
with a registry for managing and dispatching these hooks.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from attr import define
from attrs import Factory, frozen
from loguru import logger

from lsp_client.utils.types import Notification, Request, Response

from .capability import CapabilityProtocol


class ServerRequestHookExecutor[R: Request](Protocol):
    async def __call__(self, /, req: R) -> Response: ...


@frozen
class ServerRequestHook[R: Request]:
    cls: type[R]
    execute: ServerRequestHookExecutor[R]


class ServerNotificationHookExecutor[N: Notification](Protocol):
    async def __call__(self, /, noti: N) -> None: ...


@frozen
class ServerNotificationHook[N: Notification]:
    cls: type[N]
    execute: ServerNotificationHookExecutor[N]


@define
class ServerRequestHookRegistry:
    _req: dict[str, ServerRequestHook] = Factory(dict)
    _noti: dict[str, set[ServerNotificationHook]] = Factory(dict)

    def register(
        self,
        method: str,
        hook: ServerRequestHook | ServerNotificationHook,
    ) -> None:
        match hook:
            case ServerRequestHook():
                if method in self._req:
                    logger.warning(
                        "Overwriting existing request hook for method `{}`", method
                    )
                self._req[method] = hook
            case ServerNotificationHook():
                self._noti.setdefault(method, set()).add(hook)

    def get_request_hook(self, method: str) -> ServerRequestHook | None:
        return self._req.get(method)

    def get_notification_hooks(self, method: str) -> set[ServerNotificationHook]:
        return self._noti.get(method, set())


@runtime_checkable
class ServerRequestHookProtocol(CapabilityProtocol, Protocol):
    def register_server_request_hooks(
        self, registry: ServerRequestHookRegistry
    ) -> None:
        """Register request hooks to the registry."""
