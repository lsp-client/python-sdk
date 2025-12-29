from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import suppress

from attrs import frozen

from .abc import Server
from .container import ContainerServer
from .error import ServerRuntimeError
from .local import LocalServer
from .types import ServerType


@frozen
class DefaultServers:
    local: LocalServer
    container: ContainerServer

    async def iter_candidate(
        self,
        *,
        server: Server | ServerType = "local",
    ) -> AsyncIterator[Server]:
        """
        Server candidates in order of priority:
        1. User-provided server
        2. Local server (if available)
        3. Containerized server
        4. Local server with auto-install (if enabled)
        """

        match server:
            case "container":
                yield self.container
            case "local":
                yield self.local
            case Server() as server:
                yield server

        with suppress(ServerRuntimeError):
            await self.local.check_availability()
            yield self.local

        yield self.container
        yield self.local
