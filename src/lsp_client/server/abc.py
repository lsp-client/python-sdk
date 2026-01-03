from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from functools import cached_property
from typing import Self, override

import anyio
import asyncer
from anyio.abc import AnyByteReceiveStream, AnyByteSendStream
from anyio.streams.buffered import BufferedByteReceiveStream
from attrs import define, field
from loguru import logger

from lsp_client.jsonrpc.channel import ResponseTable, response_channel
from lsp_client.jsonrpc.parse import read_raw_package, write_raw_package
from lsp_client.jsonrpc.types import (
    RawNotification,
    RawPackage,
    RawRequest,
    RawResponsePackage,
)
from lsp_client.server.types import ServerRequest
from lsp_client.utils.channel import Sender
from lsp_client.utils.workspace import Workspace


@define
class Server(ABC):
    """Abstract base class for language server runtimes.

    This class defines the high-level contract for communicating with a
    language server: checking availability, sending requests and
    notifications, managing the server lifecycle, and running it within a
    workspace context.

    Unlike :class:`StreamServer`, which provides a concrete implementation
    based on byte streams and JSON-RPC protocol handling, implementations of
    :class:`Server` are free to choose how the underlying server process or
    transport is managed, as long as they honor this interface.
    """
    @abstractmethod
    async def check_availability(self) -> None:
        """Check if the server runtime is available."""

    @abstractmethod
    async def request(self, request: RawRequest) -> RawResponsePackage:
        """Send a request to the server and receive response or error."""

    @abstractmethod
    async def notify(self, notification: RawNotification) -> None:
        """Send a notification to the server."""

    @abstractmethod
    async def kill(self) -> None:
        """Terminate the server runtime."""

    @abstractmethod
    @asynccontextmanager
    def run(
        self,
        workspace: Workspace,
        sender: Sender[ServerRequest],
    ) -> AsyncGenerator[Self]: ...


@define
class StreamServer(Server):
    """Server based on byte streams with JSON-RPC protocol handling."""

    _resp_table: ResponseTable = field(factory=ResponseTable, init=False)
    """Dispatch response by response ID."""

    @property
    @abstractmethod
    def send_stream(self) -> AnyByteSendStream:
        """Stream for sending data to the server."""

    @property
    @abstractmethod
    def receive_stream(self) -> AnyByteReceiveStream:
        """Stream for receiving data from the server."""

    async def setup(self, workspace: Workspace) -> None:
        """Hook called before starting server resources.

        Use this for initialization logic that doesn't require async context managers.
        Default implementation does nothing.
        """

        return

    @asynccontextmanager
    async def manage_resources(self, workspace: Workspace) -> AsyncGenerator[None]:
        """Hook for managing server-specific resources with lifecycle.

        This is called within an async context manager, allowing subclasses to:
        - Start processes, connect sockets, etc. (on entry)
        - Clean up resources automatically (on exit)

        Default implementation does nothing. Override this in subclasses to
        setup server runtime (e.g., start process, connect socket).
        """
        yield

    async def on_started(
        self, workspace: Workspace, sender: Sender[ServerRequest]
    ) -> None:
        """Hook called after server resources are ready and dispatch loop is starting.

        Use this for post-startup initialization that needs access to the sender.
        Default implementation does nothing.
        """

        return

    async def on_shutdown(self) -> None:
        """Hook called before server resources are cleaned up.

        Use this for graceful shutdown logic before resource cleanup.
        Default implementation does nothing.
        """

        return

    @cached_property
    def _buffered_receive_stream(self) -> BufferedByteReceiveStream:
        return BufferedByteReceiveStream(self.receive_stream)

    async def kill(self) -> None:
        await self.receive_stream.aclose()

    async def send(self, package: RawPackage) -> None:
        """Send a package to the runtime."""
        await write_raw_package(self.send_stream, package)
        logger.debug("Package sent: {}", package)

    async def receive(self) -> RawPackage | None:
        try:
            package = await read_raw_package(self._buffered_receive_stream)
            logger.debug("Received package: {}", package)
            return package
        except (anyio.EndOfStream, anyio.IncompleteRead, anyio.ClosedResourceError):
            logger.debug("Stream closed")
            return None

    async def _handle_package(
        self, sender: Sender[ServerRequest], package: RawPackage
    ) -> None:
        match package:
            case {"result": _, "id": id} | {"error": _, "id": id} as resp:
                self._resp_table.send(id, resp)
            case {"id": id, "method": _} as server_req:
                tx, rx = response_channel.create()
                await sender.send((server_req, tx))
                resp = await rx.receive()
                await self.send(resp)
            case {"method": _} as noti:
                await sender.send(noti)

    async def _dispatch(self, sender: Sender[ServerRequest]) -> None:
        async with asyncer.create_task_group() as tg:
            while package := await self.receive():
                tg.soonify(self._handle_package)(sender, package)

    @override
    async def request(self, request: RawRequest) -> RawResponsePackage:
        rx = self._resp_table.reserve(request["id"])
        await self.send(request)
        return await rx.receive()

    @override
    async def notify(self, notification: RawNotification) -> None:
        await self.send(notification)

    @override
    @asynccontextmanager
    async def run(
        self, workspace: Workspace, sender: Sender[ServerRequest]
    ) -> AsyncGenerator[Self]:
        await self.setup(workspace)

        async with (
            self.manage_resources(workspace),
            asyncer.create_task_group() as tg,
        ):
            await self.on_started(workspace, sender)
            tg.soonify(self._dispatch)(sender)

            try:
                yield self
            finally:
                await self.on_shutdown()
