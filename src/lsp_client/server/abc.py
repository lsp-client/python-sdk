from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from functools import cached_property
from typing import Self

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


@define(kw_only=True)
class Server(ABC):
    """Base server implementation with JSON-RPC protocol handling."""

    _resp_table: ResponseTable = field(factory=ResponseTable, init=False)

    @property
    @abstractmethod
    def send_stream(self) -> AnyByteSendStream:
        """Stream for sending data to the server."""

    @property
    @abstractmethod
    def receive_stream(self) -> AnyByteReceiveStream:
        """Stream for receiving data from the server."""

    @cached_property
    def _buffered_receive_stream(self) -> BufferedByteReceiveStream:
        return BufferedByteReceiveStream(self.receive_stream)

    @abstractmethod
    async def check_availability(self) -> None:
        """Check if the server runtime is available."""

    async def kill(self) -> None:
        await self.receive_stream.aclose()

    async def send(self, package: RawPackage) -> None:
        """Send a package to the runtime."""
        await write_raw_package(self.send_stream, package)
        logger.debug("Package sent: {}", package)

    async def receive(self) -> RawPackage | None:
        """Receive a package from the runtime."""

        try:
            package = await read_raw_package(self._buffered_receive_stream)
            logger.debug("Received package: {}", package)
            return package
        except (anyio.EndOfStream, anyio.IncompleteRead, anyio.ClosedResourceError):
            logger.debug("Stream closed")
            return None

    async def iter_receive(self) -> AsyncGenerator[RawPackage]:
        while package := await self.receive():
            yield package

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

    async def request(self, request: RawRequest) -> RawResponsePackage:
        rx = self._resp_table.reserve(request["id"])
        await self.send(request)
        return await rx.receive()

    async def notify(self, notification: RawNotification) -> None:
        await self.send(notification)

    @asynccontextmanager
    async def run(
        self, workspace: Workspace, sender: Sender[ServerRequest]
    ) -> AsyncGenerator[Self]:
        """Run the server."""
        async with asyncer.create_task_group() as tg:
            tg.soonify(self._dispatch)(sender)
            yield self
