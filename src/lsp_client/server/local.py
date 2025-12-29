from __future__ import annotations

from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from functools import cached_property
from pathlib import Path
from typing import Protocol, Self, final, override

import aioshutil
import anyio
import asyncer
from anyio.abc import AnyByteSendStream, Process
from anyio.streams.buffered import BufferedByteReceiveStream
from attrs import Factory, define, field
from loguru import logger

from lsp_client.env import disable_auto_installation
from lsp_client.jsonrpc.parse import read_raw_package, write_raw_package
from lsp_client.jsonrpc.types import RawPackage
from lsp_client.server.types import ServerRequest
from lsp_client.utils.channel import Sender
from lsp_client.utils.workspace import Workspace

from .abc import Server
from .error import ServerRuntimeError


class EnsureInstalledProtocol(Protocol):
    async def __call__(self) -> None: ...


@final
@define
class LocalServer(Server):
    program: str
    args: Sequence[str] = Factory(list)

    cwd: Path = Factory(Path.cwd)
    env: dict[str, str] | None = None
    shutdown_timeout: float = 5.0

    ensure_installed: EnsureInstalledProtocol | None = None

    _process: Process = field(init=False, default=None)

    @cached_property
    def stdin(self) -> AnyByteSendStream:
        stdin = self._process.stdin
        assert stdin, "Process stdin is not available"
        return stdin

    @cached_property
    def stdout(self) -> BufferedByteReceiveStream:
        stdout = self._process.stdout
        assert stdout, "Process stdout is not available"
        return BufferedByteReceiveStream(stdout)

    @cached_property
    def stderr(self) -> BufferedByteReceiveStream:
        stderr = self._process.stderr
        assert stderr, "Process stderr is not available"
        return BufferedByteReceiveStream(stderr)

    @override
    async def send(self, package: RawPackage) -> None:
        await write_raw_package(self.stdin, package)
        logger.debug("Package sent: {}", package)

    @override
    async def receive(self) -> RawPackage | None:
        try:
            package = await read_raw_package(self.stdout)
            logger.debug("Received package: {}", package)
            return package
        except (anyio.EndOfStream, anyio.IncompleteRead, anyio.ClosedResourceError):
            logger.debug("Process stdout closed")
            return None

    @override
    async def kill(self) -> None:
        logger.debug("Killing process")
        if self._process:
            self._process.kill()
            await self._process.aclose()

    @override
    async def check_availability(self) -> None:
        if not await aioshutil.which(self.program):
            raise ServerRuntimeError(
                self, f"Program '{self.program}' not found in PATH."
            )

    @asynccontextmanager
    async def run_process(self, workspace: Workspace) -> AsyncGenerator[None]:
        try:
            await self.check_availability()
        except ServerRuntimeError as e:
            if disable_auto_installation():
                raise ServerRuntimeError(self, "auto-installation is disabled.") from e
            elif self.ensure_installed:
                await self.ensure_installed()
            else:
                raise ServerRuntimeError(
                    self, "no installation method is provided."
                ) from e

        command = [self.program, *self.args]
        logger.debug("Running with command: {}", command)

        try:
            self._process = await anyio.open_process(
                command, cwd=self.cwd, env=self.env
            )
            yield
        except (OSError, RuntimeError) as e:
            raise ServerRuntimeError(self, "Failed to start server process") from e
        finally:
            try:
                if self._process.returncode is None:
                    self._process.terminate()

                with anyio.fail_after(self.shutdown_timeout):
                    if (returncode := await self._process.wait()) != 0:
                        logger.warning("Process exited with code {}", returncode)
                    else:
                        logger.debug("Process exited successfully")
            except (TimeoutError, OSError):
                logger.warning("Process shutdown failed, killing process")
                await self.kill()

    @asynccontextmanager
    async def run(
        self,
        workspace: Workspace,
        *,
        sender: Sender[ServerRequest] | None = None,
    ) -> AsyncGenerator[Self]:
        async with (
            self.run_process(workspace),
            asyncer.create_task_group() as tg,
        ):
            tg.soonify(self._dispatch)(sender)
            yield self
