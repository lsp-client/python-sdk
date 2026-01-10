from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Protocol, override, runtime_checkable

from loguru import logger

from lsp_client.capability.notification.did_change_configuration import (
    WithNotifyDidChangeConfiguration,
)
from lsp_client.protocol import (
    CapabilityClientProtocol,
    ServerRequestHook,
    ServerRequestHookProtocol,
    ServerRequestHookRegistry,
    WorkspaceCapabilityProtocol,
)
from lsp_client.utils.config import ConfigurationMap
from lsp_client.utils.types import lsp_type


@runtime_checkable
class WithRespondConfigurationRequest(
    WorkspaceCapabilityProtocol,
    ServerRequestHookProtocol,
    CapabilityClientProtocol,
    Protocol,
):
    """
    `workspace/configuration` - https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_configuration
    """

    def create_default_config(self) -> dict[str, Any] | None:
        return

    @override
    @classmethod
    def iter_methods(cls) -> Iterator[str]:
        yield from super().iter_methods()
        yield from (lsp_type.WORKSPACE_CONFIGURATION,)

    @override
    @classmethod
    def register_workspace_capability(
        cls, cap: lsp_type.WorkspaceClientCapabilities
    ) -> None:
        super().register_workspace_capability(cap)
        cap.configuration = True

    @override
    @classmethod
    def check_server_capability(cls, cap: lsp_type.ServerCapabilities) -> None:
        super().check_server_capability(cap)

    def get_configuration(self, scope_uri: str | None, section: str | None) -> Any:
        """
        Get the configuration value for the given scope URI and section.

        Default implementation uses `self.configuration_map` if available.
        """

        if not (config := self.get_config_map()):
            return None
        return config.get(scope_uri, section)

    async def _respond_configuration(
        self, params: lsp_type.ConfigurationParams
    ) -> list[Any]:
        logger.debug("Responding to configuration request")

        return [
            self.get_configuration(item.scope_uri, item.section)
            for item in params.items
        ]

    async def respond_configuration_request(
        self, req: lsp_type.ConfigurationRequest
    ) -> lsp_type.ConfigurationResponse:
        return lsp_type.ConfigurationResponse(
            id=req.id,
            result=await self._respond_configuration(req.params),
        )

    @override
    def register_server_request_hooks(
        self, registry: ServerRequestHookRegistry
    ) -> None:
        super().register_server_request_hooks(registry)

        # Notify server when configuration changes
        if isinstance(self, WithNotifyDidChangeConfiguration):

            async def notify_change(config_map: ConfigurationMap) -> None:
                with logger.contextualize(method="didChangeConfiguration"):
                    logger.debug(
                        "Configuration changed: {}, notifying server", config_map
                    )
                    await self.notify_change_configuration()

            self.get_config_map().on_change(notify_change)

        registry.register(
            lsp_type.WORKSPACE_CONFIGURATION,
            ServerRequestHook(
                cls=lsp_type.ConfigurationRequest,
                execute=self.respond_configuration_request,
            ),
        )
