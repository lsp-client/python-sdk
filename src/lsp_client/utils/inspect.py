from __future__ import annotations

import itertools
from collections.abc import AsyncGenerator

from attrs import frozen

from lsp_client.capability.build import build_client_capabilities
from lsp_client.capability.notification import capabilities as notification_capabilities
from lsp_client.capability.request import capabilities as request_capabilities
from lsp_client.capability.server_notification import (
    capabilities as server_notification_capabilities,
)
from lsp_client.capability.server_request import (
    capabilities as server_request_capabilities,
)
from lsp_client.client.abc import Client
from lsp_client.jsonrpc.convert import lsp_type, request_serialize, response_deserialize
from lsp_client.server.abc import Server
from lsp_client.server.types import ServerRequest
from lsp_client.utils.channel import channel
from lsp_client.utils.workspace import DEFAULT_WORKSPACE


@frozen
class CapabilityInspectResult:
    capability: str
    client: bool
    server: bool


async def inspect_capabilities(
    server: Server, client_cls: type[Client]
) -> AsyncGenerator[CapabilityInspectResult, None]:
    """Inspect server capabilities and compare with client capabilities.

    This function starts the server if it's not already running and sends
    an initialize request to get server capabilities.
    """
    if not __debug__:
        raise RuntimeError("inspect_capabilities can only be used in debug mode")

    async with (
        channel[ServerRequest].create() as (sender, _),
        server.run(DEFAULT_WORKSPACE, sender=sender),
    ):
        req = lsp_type.InitializeRequest(
            id="initialize",
            params=lsp_type.InitializeParams(
                capabilities=build_client_capabilities(client_cls)
            ),
        )
        raw_resp = await server.request(request_serialize(req))
        resp = response_deserialize(raw_resp, lsp_type.InitializeResponse)

    server_capabilities = resp.capabilities

    for cap in itertools.chain(
        request_capabilities,
        notification_capabilities,
        server_request_capabilities,
        server_notification_capabilities,
    ):
        client_available = issubclass(client_cls, cap)

        try:
            cap.check_server_capability(server_capabilities)
            server_available = True
        except AssertionError:
            server_available = False

        for method in cap.iter_methods():
            yield CapabilityInspectResult(
                capability=method,
                client=client_available,
                server=server_available,
            )
