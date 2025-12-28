from __future__ import annotations

import platform
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import final, override

import anyio
import tenacity
from anyio.abc import ByteStream, IPAddressType
from anyio.streams.buffered import BufferedByteReceiveStream
from attrs import define, field
from loguru import logger

from lsp_client.jsonrpc.parse import read_raw_package, write_raw_package
from lsp_client.jsonrpc.types import RawPackage
from lsp_client.server.exception import ServerRuntimeError
from lsp_client.utils.types import AnyPath
from lsp_client.utils.workspace import Workspace

from .abc import Server

type TCPSocket = tuple[IPAddressType, int]
"""(host, port)"""

type UnixSocket = AnyPath


@final
@define
class SocketServer(Server):
    """Runtime for socket backend, e.g. connecting to a remote LSP server via TCP or Unix socket."""

    connection: TCPSocket | UnixSocket
    """Connection information, either (host, port) for TCP or path for Unix socket."""

    timeout: float = 10.0
    """Timeout for connecting to the socket."""

    _stream: ByteStream = field(init=False)
    _buffered: BufferedByteReceiveStream = field(init=False)

    @tenacity.retry(
        stop=tenacity.stop_after_delay(10),
        wait=tenacity.wait_exponential(multiplier=0.1, max=1),
        reraise=True,
    )
    async def connect(self) -> ByteStream:
        match self.connection:
            case (host, port):
                logger.debug("Connecting to {}:{}", host, port)
                return await anyio.connect_tcp(host, port)
            case path:
                if platform.platform().startswith("Windows"):
                    raise ServerRuntimeError(
                        self, "Unix sockets are not supported on Windows"
                    )
                logger.debug("Connecting to {}", path)
                return await anyio.connect_unix(str(path))

    @override
    async def check_availability(self) -> None:
        try:
            stream = await self.connect()
            await stream.aclose()
        except anyio.ConnectionFailed as e:
            raise ServerRuntimeError(self, f"Failed to connect to socket: {e}") from e

    @override
    async def send(self, package: RawPackage) -> None:
        if self._stream is None:
            raise RuntimeError("SocketServer is not running")
        await write_raw_package(self._stream, package)

    @override
    async def receive(self) -> RawPackage | None:
        if self._buffered is None:
            raise RuntimeError("SocketServer is not running")
        try:
            return await read_raw_package(self._buffered)
        except (anyio.EndOfStream, anyio.IncompleteRead, anyio.ClosedResourceError):
            logger.debug("Socket closed")
            return

    @override
    async def kill(self) -> None:
        await self._stream.aclose()

    @override
    @asynccontextmanager
    async def run_process(self, workspace: Workspace) -> AsyncGenerator[None]:
        await self.check_availability()

        stream: ByteStream = await self.connect()

        self._stream = stream
        self._buffered = BufferedByteReceiveStream(stream)

        async with stream:
            yield
