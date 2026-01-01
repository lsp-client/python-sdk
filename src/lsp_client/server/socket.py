from __future__ import annotations

import platform
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Self, final, override

import anyio
import tenacity
from anyio.abc import AnyByteReceiveStream, AnyByteSendStream, ByteStream, IPAddressType
from attrs import define, field
from loguru import logger

from lsp_client.server.error import ServerRuntimeError
from lsp_client.server.types import ServerRequest
from lsp_client.utils.channel import Sender
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

    @override
    async def check_availability(self) -> None:
        try:
            stream = await self.connect()
            await stream.aclose()
        except anyio.ConnectionFailed as e:
            raise ServerRuntimeError(self, f"Failed to connect to socket: {e}") from e

    @property
    @override
    def send_stream(self) -> AnyByteSendStream:
        return self._stream

    @property
    @override
    def receive_stream(self) -> AnyByteReceiveStream:
        return self._stream

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
    async def kill(self) -> None:
        await self._stream.aclose()

    @override
    @asynccontextmanager
    async def run(
        self, workspace: Workspace, sender: Sender[ServerRequest]
    ) -> AsyncGenerator[Self]:
        self._stream = await self.connect()

        async with (
            self._stream,
            super().run(workspace, sender=sender),
        ):
            yield self
