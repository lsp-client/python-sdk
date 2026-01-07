from __future__ import annotations

import shutil
import sys
from functools import partial
from subprocess import CalledProcessError
from typing import Any, override

import anyio
from attrs import define
from loguru import logger

from lsp_client.capability.notification import (
    WithNotifyDidChangeConfiguration,
    WithNotifyDidCreateFiles,
    WithNotifyDidDeleteFiles,
    WithNotifyDidRenameFiles,
)
from lsp_client.capability.request import (
    WithRequestCallHierarchy,
    WithRequestCodeAction,
    WithRequestCompletion,
    WithRequestDeclaration,
    WithRequestDefinition,
    WithRequestDocumentSymbol,
    WithRequestHover,
    WithRequestReferences,
    WithRequestRename,
    WithRequestSignatureHelp,
    WithRequestTypeDefinition,
    WithRequestWillCreateFiles,
    WithRequestWillDeleteFiles,
    WithRequestWillRenameFiles,
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

BasedpyrightContainerServer = partial(
    ContainerServer, image="ghcr.io/lsp-client/basedpyright:latest"
)


async def ensure_basedpyright_installed() -> None:
    if shutil.which("basedpyright-langserver"):
        return

    installers = [
        (["uv", "tool", "install", "basedpyright"], "uv"),
        (["npm", "install", "-g", "basedpyright"], "npm"),
        ([sys.executable, "-m", "pip", "install", "basedpyright"], "pip"),
    ]

    for cmd, name in installers:
        if shutil.which(cmd[0]):
            try:
                logger.info("Attempting to install basedpyright via {}...", name)
                await anyio.run_process(cmd)
                return
            except CalledProcessError:
                continue

    raise ServerInstallationError(
        "Could not install basedpyright. Please install it manually with 'uv tool install basedpyright', 'npm install -g basedpyright' or 'pip install basedpyright'."
    )


BasedpyrightLocalServer = partial(
    LocalServer,
    program="basedpyright-langserver",
    args=["--stdio"],
    ensure_installed=ensure_basedpyright_installed,
)


@define
class BasedpyrightClient(
    PythonClientBase,
    WithNotifyDidChangeConfiguration,
    WithNotifyDidCreateFiles,
    WithNotifyDidRenameFiles,
    WithNotifyDidDeleteFiles,
    WithRequestCallHierarchy,
    WithRequestCodeAction,
    WithRequestCompletion,
    WithRequestDeclaration,
    WithRequestDefinition,
    WithRequestDocumentSymbol,
    WithRequestHover,
    WithRequestReferences,
    WithRequestRename,
    WithRequestSignatureHelp,
    WithRequestTypeDefinition,
    WithRequestWillCreateFiles,
    WithRequestWillRenameFiles,
    WithRequestWillDeleteFiles,
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
    - Homepage: https://github.com/detachhead/basedpyright
    - Doc: https://github.com/detachhead/basedpyright
    - Github: https://github.com/detachhead/basedpyright
    """

    @classmethod
    @override
    def create_default_servers(cls) -> DefaultServers:
        return DefaultServers(
            local=BasedpyrightLocalServer(),
            container=BasedpyrightContainerServer(),
        )

    @override
    def check_server_compatibility(self, info: lsp_type.ServerInfo | None) -> None:
        return

    @override
    def create_default_config(self) -> dict[str, Any] | None:
        """
        https://github.com/detachhead/basedpyright#settings
        """
        analysis = {
            "analysis": {
                "autoImportCompletions": True,
                "autoSearchPaths": True,
                "diagnosticMode": "openFilesOnly",
                "indexing": True,
                "typeCheckingMode": "recommended",
                "inlayHints": {
                    "variableTypes": True,
                    "functionReturnTypes": True,
                    "callArgumentNames": True,
                    "pytestParameters": True,
                },
            }
        }
        return {
            "python": analysis,
            "basedpyright": analysis,
        }
