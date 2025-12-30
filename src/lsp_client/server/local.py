from __future__ import annotations

from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Protocol, Self, final, override

import aioshutil
import anyio
from anyio.abc import AnyByteReceiveStream, AnyByteSendStream, Process
from attrs import Factory, define, field
from loguru import logger

from lsp_client.env import disable_auto_installation
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

    @property
    @override
    def send_stream(self) -> AnyByteSendStream:
        stdin = self._process.stdin
        assert stdin, "Process stdin is not available"
        return stdin

    @property
    @override
    def receive_stream(self) -> AnyByteReceiveStream:
        stdout = self._process.stdout
        assert stdout, "Process stdout is not available"
        return stdout

    @property
    def stderr(self) -> AnyByteReceiveStream:
        stderr = self._process.stderr
        assert stderr, "Process stderr is not available"
        return stderr

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

    @override
    @asynccontextmanager
    async def run(
        self, workspace: Workspace, sender: Sender[ServerRequest]
    ) -> AsyncGenerator[Self]:
        async with (
            self.run_process(workspace),
            super().run(workspace, sender=sender),
        ):
            yield self
