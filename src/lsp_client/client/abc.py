from __future__ import annotations

import os
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress
from functools import cached_property
from pathlib import Path
from typing import Any, Literal, Self, override

import anyio
import asyncer
from anyio import AsyncContextManagerMixin
from attrs import Factory, define, field
from loguru import logger

from lsp_client.capability.build import (
    build_client_capabilities,
    build_server_request_hooks,
)
from lsp_client.capability.notification import WithNotifyTextDocumentSynchronize
from lsp_client.client.buffer import LSPFileBuffer
from lsp_client.jsonrpc.convert import (
    notification_serialize,
    request_deserialize,
    request_serialize,
    response_deserialize,
    response_serialize,
)
from lsp_client.protocol import CapabilityClientProtocol, CapabilityProtocol
from lsp_client.server import DefaultServers, Server, ServerRuntimeError
from lsp_client.server.types import ServerRequest
from lsp_client.utils.channel import Receiver, channel
from lsp_client.utils.config import ConfigurationMap
from lsp_client.utils.types import AnyPath, Notification, Request, Response, lsp_type
from lsp_client.utils.workspace import (
    DEFAULT_WORKSPACE_DIR,
    RawWorkspace,
    Workspace,
    format_workspace,
)


@define
class Client(
    # text sync support is mandatory
    WithNotifyTextDocumentSynchronize,
    CapabilityClientProtocol,
    AsyncContextManagerMixin,
    ABC,
):
    _server_arg: Server | Literal["container", "local"] | None = field(
        alias="server", default=None
    )
    """LSP server to use. Can be a Server instance, 'container', or 'local'."""

    _workspace_arg: RawWorkspace = field(alias="workspace", factory=Path.cwd)
    """Workspace directory or configuration."""

    sync_file: bool = True
    """Whether to sync file contents with the server."""

    request_timeout: float = 5.0
    """Timeout in seconds for JSON-RPC requests."""

    initialization_options: dict = field(factory=dict)
    """Custom initialization options for the server."""

    unmanaged: bool = False
    """If True, skip automatic lifecycle management (initialize/shutdown)."""

    _server: Server = field(init=False)
    _buffer: LSPFileBuffer = field(factory=LSPFileBuffer, init=False)
    _config: ConfigurationMap = Factory(ConfigurationMap)

    @cached_property
    def _workspace(self) -> Workspace:
        return format_workspace(self._workspace_arg)

    async def _iter_candidate_servers(self) -> AsyncGenerator[Server]:
        """
        Server candidates in order of priority:
        1. User-provided server
        2. Local server (if available)
        3. Containerized server
        4. Local server with auto-install (if enabled)
        """

        defaults = self.create_default_servers()

        match self._server_arg:
            case "container":
                yield defaults.container
            case "local":
                yield defaults.local
            case Server() as server:
                yield server

        with suppress(ServerRuntimeError):
            await defaults.local.check_availability()
            yield defaults.local

        yield defaults.container
        yield defaults.local

    @asynccontextmanager
    async def run_server(
        self,
    ) -> AsyncGenerator[tuple[Server, Receiver[ServerRequest]]]:
        async with channel[ServerRequest].create() as (sender, receiver):
            errors: list[ServerRuntimeError] = []
            async for candidate in self._iter_candidate_servers():
                try:
                    async with candidate.run(self._workspace, sender=sender) as server:
                        yield server, receiver
                        return
                except ServerRuntimeError as e:
                    logger.debug("Failed to start server {}: {}", candidate, e)
                    errors.append(e)

            raise ExceptionGroup(
                f"All servers failed to start for {type(self).__name__}", errors
            )

    @override
    def get_workspace(self) -> Workspace:
        return self._workspace

    @override
    def get_config_map(self) -> ConfigurationMap:
        return self._config

    def get_server(self) -> Server:
        return self._server

    @classmethod
    @abstractmethod
    def create_default_servers(cls) -> DefaultServers:
        """Create default servers for this client."""

    def create_default_config(self) -> dict[str, Any] | None:
        """Create default configuration map for this client."""
        return

    @abstractmethod
    def check_server_compatibility(self, info: lsp_type.ServerInfo | None) -> None:
        """Check if the available server capabilities are compatible with the client."""

    @override
    @asynccontextmanager
    async def open_files(self, *file_paths: AnyPath) -> AsyncGenerator[None]:
        if not self.sync_file:
            yield
            return

        file_uris = [self.as_uri(file_path) for file_path in file_paths]

        if not file_uris:
            yield
            return

        buffer_items = await self._buffer.open(file_uris)
        async with asyncer.create_task_group() as tg:
            for item in buffer_items:
                tg.soonify(self.notify_text_document_opened)(
                    file_path=item.file_path,
                    file_content=item.content,
                )

        try:
            yield
        finally:
            closed_items = self._buffer.close(item.file_uri for item in buffer_items)

            async with asyncer.create_task_group() as tg:
                for item in closed_items:
                    tg.soonify(self.notify_text_document_closed)(item.file_path)

    @override
    async def request[R](
        self,
        req: Request,
        schema: type[Response[R]],
    ) -> R:
        req = request_serialize(req)
        with anyio.fail_after(self.request_timeout):
            raw_resp = await self.get_server().request(req)
            return response_deserialize(raw_resp, schema)

    @override
    async def notify(self, msg: Notification) -> None:
        noti = notification_serialize(msg)
        with anyio.fail_after(self.request_timeout):
            await self.get_server().notify(noti)

    async def _dispatch_server_requests(
        self, receiver: Receiver[ServerRequest]
    ) -> None:
        hooks = build_server_request_hooks(self)

        async def dispatch(req: ServerRequest) -> None:
            match req:
                case (req, tx):
                    if hook := hooks.get_request_hook(req["method"]):
                        req = request_deserialize(req, hook.cls)
                        resp = await hook.execute(req)
                        tx.send(response_serialize(resp))
                case noti:
                    if noti_hooks := hooks.get_notification_hooks(noti["method"]):
                        for hook in noti_hooks:
                            noti = request_deserialize(noti, hook.cls)
                            tg.soonify(hook.execute)(noti)

        async with asyncer.create_task_group() as tg:
            async for req in receiver:
                tg.soonify(dispatch)(req)

    async def _initialize(self, params: lsp_type.InitializeParams) -> None:
        result = await self.request(
            lsp_type.InitializeRequest(id="initialize", params=params),
            schema=lsp_type.InitializeResponse,
        )
        server_capabilities = result.capabilities
        server_info = result.server_info

        if __debug__:
            # ensure the server version is compatible with the client
            self.check_server_compatibility(server_info)

            # ensure all client capabilities are supported by the server
            if isinstance(self, CapabilityProtocol):
                self.check_server_capability(server_capabilities)
        else:
            logger.debug("Skip server check in optimized mode")

        await self.notify(
            lsp_type.InitializedNotification(params=lsp_type.InitializedParams())
        )

    async def _shutdown(self):
        """
        `shutdown` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#shutdown
        """

        _ = await self.request(
            lsp_type.ShutdownRequest(
                id="shutdown",
            ),
            schema=lsp_type.ShutdownResponse,
        )

    async def _exit(self) -> None:
        """
        `exit` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#exit
        """

        await self.notify(lsp_type.ExitNotification())

    @override
    @asynccontextmanager
    @logger.catch(reraise=True)
    async def __asynccontextmanager__(self) -> AsyncGenerator[Self]:
        async with (
            asyncer.create_task_group() as tg,
            self.run_server() as (server, receiver),
        ):
            self._server = server

            # start to receive server requests here,
            # since server notification can be sent before `initialize`
            tg.soonify(self._dispatch_server_requests)(receiver)

            if not self.unmanaged:
                client_capabilities = build_client_capabilities(self.__class__)
                root_workspace = self.get_workspace().get(DEFAULT_WORKSPACE_DIR)
                root_path = root_workspace.path.as_posix() if root_workspace else None
                root_uri = root_workspace.uri if root_workspace else None

                _ = await self._initialize(
                    lsp_type.InitializeParams(
                        capabilities=client_capabilities,
                        process_id=os.getpid(),
                        client_info=lsp_type.ClientInfo(
                            name="lsp-lient",
                            version="1.81.0-insider",
                        ),
                        locale="en-us",
                        # if single workspace root provided,
                        # set both `root_path` and `root_uri` for compatibility
                        root_path=root_path,
                        root_uri=root_uri,
                        initialization_options=self.initialization_options,
                        trace=lsp_type.TraceValue.Verbose,
                        workspace_folders=self._workspace.to_folders(),
                    )
                )

                if init_config := self.create_default_config():
                    await self._config.update_global(init_config)

            try:
                yield self
            finally:
                if not self.unmanaged:
                    _ = await self._shutdown()
                    await self._exit()
                else:
                    await self.get_server().kill()
                    tg.cancel_scope.cancel()
