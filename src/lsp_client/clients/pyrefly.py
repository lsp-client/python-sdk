from __future__ import annotations

import shutil
from functools import partial
from subprocess import CalledProcessError
from typing import Any, override

import anyio
from attrs import define
from loguru import logger

from lsp_client.capability.notification import (
    WithNotifyDidChangeConfiguration,
)
from lsp_client.capability.request import (
    WithRequestCallHierarchy,
    WithRequestCodeAction,
    WithRequestCompletion,
    WithRequestDeclaration,
    WithRequestDefinition,
    WithRequestDocumentSymbol,
    WithRequestHover,
    WithRequestImplementation,
    WithRequestInlayHint,
    WithRequestReferences,
    WithRequestSignatureHelp,
    WithRequestTypeDefinition,
    WithRequestWorkspaceSymbol,
)
from lsp_client.capability.server_notification import (
    WithReceiveLogMessage,
    WithReceiveLogTrace,
    WithReceivePublishDiagnostics,
    WithReceiveShowMessage,
)
from lsp_client.capability.server_request import (
    WithRespondConfigurationRequest,
    WithRespondInlayHintRefresh,
    WithRespondShowDocumentRequest,
    WithRespondShowMessageRequest,
    WithRespondWorkspaceFoldersRequest,
)
from lsp_client.clients.base import PythonClientBase
from lsp_client.server import DefaultServers, ServerInstallationError
from lsp_client.server.container import ContainerServer
from lsp_client.server.local import LocalServer
from lsp_client.utils.types import lsp_type

PyreflyContainerServer = partial(
    ContainerServer, image="ghcr.io/lsp-client/pyrefly:latest"
)


async def ensure_pyrefly_installed() -> None:
    """When using local runtime, check and install the server if necessary."""
    if shutil.which("pyrefly"):
        return

    logger.warning("pyrefly not found, attempting to install...")

    try:
        if shutil.which("uv"):
            await anyio.run_process(["uv", "tool", "install", "pyrefly"])
        elif shutil.which("pip"):
            await anyio.run_process(["pip", "install", "pyrefly"])
        logger.info("Successfully installed pyrefly via uv tool")
    except CalledProcessError as e:
        raise ServerInstallationError(
            "Could not install pyrefly. Please install it manually with 'pip install pyrefly'. "
            "See https://pyrefly.org/ for more information."
        ) from e


PyreflyLocalServer = partial(
    LocalServer,
    program="pyrefly",
    args=["lsp"],
    ensure_installed=ensure_pyrefly_installed,
)


@define
class PyreflyClient(
    PythonClientBase,
    WithNotifyDidChangeConfiguration,
    WithRequestCallHierarchy,
    WithRequestCodeAction,
    WithRequestCompletion,
    WithRequestDeclaration,
    WithRequestDefinition,
    WithRequestDocumentSymbol,
    WithRequestHover,
    WithRequestImplementation,
    WithRequestInlayHint,
    WithRequestReferences,
    WithRequestSignatureHelp,
    WithRequestTypeDefinition,
    WithRequestWorkspaceSymbol,
    WithReceiveLogMessage,
    WithReceiveLogTrace,
    WithReceivePublishDiagnostics,
    WithReceiveShowMessage,
    WithRespondConfigurationRequest,
    WithRespondInlayHintRefresh,
    WithRespondShowDocumentRequest,
    WithRespondShowMessageRequest,
    WithRespondWorkspaceFoldersRequest,
):
    """
    - Language: Python
    - Homepage: https://pyrefly.org/
    - Doc: https://pyrefly.org/en/docs/
    - Github: https://github.com/facebook/pyrefly
    - VSCode Extension: https://github.com/facebook/pyrefly/tree/main/lsp
    """

    @classmethod
    @override
    def create_default_servers(cls) -> DefaultServers:
        return DefaultServers(
            local=PyreflyLocalServer(),
            container=PyreflyContainerServer(),
        )

    @override
    def check_server_compatibility(self, info: lsp_type.ServerInfo | None) -> None:
        return

    @override
    def create_default_config(self) -> dict[str, Any] | None:
        """
        https://pyrefly.org/en/docs/configuration
        """
        return {
            "pyrefly": {
                "inlayHints": {
                    "variableTypes": True,
                    "functionReturnTypes": True,
                    "parameterTypes": True,
                },
                "diagnostics": {
                    "enable": True,
                },
                "completion": {
                    "autoImports": True,
                },
            }
        }
