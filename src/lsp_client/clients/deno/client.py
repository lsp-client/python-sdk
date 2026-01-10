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
    WithDocumentDiagnostic,
    WithRequestCallHierarchy,
    WithRequestCodeAction,
    WithRequestCompletion,
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
    WithReceiveLogTrace,
    WithReceivePublishDiagnostics,
    WithReceiveShowMessage,
)
from lsp_client.capability.server_notification.log_message import WithReceiveLogMessage
from lsp_client.capability.server_request import (
    WithRespondConfigurationRequest,
    WithRespondInlayHintRefresh,
    WithRespondShowDocumentRequest,
    WithRespondShowMessageRequest,
    WithRespondWorkspaceFoldersRequest,
)
from lsp_client.client.abc import Client
from lsp_client.protocol.lang import LanguageConfig
from lsp_client.server import DefaultServers, ServerInstallationError
from lsp_client.server.container import ContainerServer
from lsp_client.server.local import LocalServer
from lsp_client.utils.types import lsp_type

from .extension import (
    WithReceiveDenoRegistryStatus,
    WithReceiveDenoTestModule,
    WithReceiveDenoTestModuleDelete,
    WithReceiveDenoTestRunProgress,
    WithRequestDenoCache,
    WithRequestDenoPerformance,
    WithRequestDenoReloadImportRegistries,
    WithRequestDenoTask,
    WithRequestDenoTestRun,
    WithRequestDenoTestRunCancel,
    WithRequestDenoVirtualTextDocument,
)

DenoContainerServer = partial(ContainerServer, image="ghcr.io/lsp-client/deno:latest")


async def ensure_deno_installed() -> None:
    if shutil.which("deno"):
        return

    logger.warning("deno not found, attempting to install...")

    try:
        # Use shell to execute the piped command
        await anyio.run_process(
            ["sh", "-c", "curl -fsSL https://deno.land/install.sh | sh"]
        )
        logger.info("Successfully installed deno via shell script")
    except CalledProcessError as e:
        raise ServerInstallationError(
            "Could not install deno. Please install it manually with:\n"
            "curl -fsSL https://deno.land/install.sh | sh\n\n"
            "See https://deno.land/ for more information."
        ) from e
    else:
        return


DenoLocalServer = partial(
    LocalServer,
    program="deno",
    args=["lsp"],
    ensure_installed=ensure_deno_installed,
)


@define
class DenoClient(
    Client,
    WithNotifyDidChangeConfiguration,
    WithRequestCodeAction,
    WithRequestHover,
    WithRequestCompletion,
    WithRequestDefinition,
    WithRequestReferences,
    WithRequestImplementation,
    WithRequestTypeDefinition,
    WithRequestCallHierarchy,
    WithRequestDocumentSymbol,
    WithRequestInlayHint,
    WithDocumentDiagnostic,
    WithRequestSignatureHelp,
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
    WithRequestDenoCache,
    WithRequestDenoPerformance,
    WithRequestDenoReloadImportRegistries,
    WithRequestDenoVirtualTextDocument,
    WithRequestDenoTask,
    WithRequestDenoTestRun,
    WithRequestDenoTestRunCancel,
    WithReceiveDenoRegistryStatus,
    WithReceiveDenoTestModule,
    WithReceiveDenoTestModuleDelete,
    WithReceiveDenoTestRunProgress,
):
    """
    - Language: TypeScript, JavaScript
    - Homepage: https://deno.land/
    - Doc: https://docs.deno.com/runtime/reference/lsp_integration/
    - Github: https://github.com/denoland/deno
    - VSCode Extension: https://marketplace.visualstudio.com/items?itemName=denoland.vscode-deno
    """

    @override
    @classmethod
    def get_language_config(cls) -> LanguageConfig:
        return LanguageConfig(
            kind=lsp_type.LanguageKind.TypeScript,
            suffixes=[".ts", ".tsx", ".js", ".jsx", ".mjs"],
            project_files=["deno.json", "deno.jsonc"],
        )

    @classmethod
    @override
    def create_default_servers(cls) -> DefaultServers:
        return DefaultServers(
            local=DenoLocalServer(),
            container=DenoContainerServer(),
        )

    @override
    def check_server_compatibility(self, info: lsp_type.ServerInfo | None) -> None:
        return

    @override
    def create_default_config(self) -> dict[str, Any] | None:
        """
        https://docs.deno.com/runtime/reference/lsp_integration/#configuration
        """
        return {
            "deno": {
                "enable": True,
                "unstable": True,
                "lint": True,
                "suggest": {
                    "autoImports": True,
                    "completeFunctionCalls": True,
                    "names": True,
                    "paths": True,
                    "imports": {
                        "autoDiscover": True,
                        "hosts": {
                            "https://deno.land": True,
                            "https://esm.sh": True,
                        },
                    },
                },
                "inlayHints": {
                    "parameterNames": {"enabled": "all"},
                    "parameterTypes": {"enabled": True},
                    "variableTypes": {"enabled": True},
                    "propertyDeclarationTypes": {"enabled": True},
                    "functionLikeReturnTypes": {"enabled": True},
                    "enumMemberValues": {"enabled": True},
                },
                "codeLens": {
                    "implementations": True,
                    "references": True,
                    "referencesAllFunctions": True,
                    "test": True,
                },
            }
        }
