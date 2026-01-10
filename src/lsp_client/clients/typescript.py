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
from lsp_client.clients.base import TypeScriptClientBase
from lsp_client.server import DefaultServers, ServerInstallationError
from lsp_client.server.container import ContainerServer
from lsp_client.server.local import LocalServer
from lsp_client.utils.types import lsp_type

TypescriptContainerServer = partial(
    ContainerServer, image="ghcr.io/lsp-client/typescript:latest"
)


async def ensure_typescript_installed() -> None:
    if shutil.which("typescript-language-server"):
        return

    logger.warning(
        "typescript-language-server not found, attempting to install via npm..."
    )

    try:
        # typescript-language-server requires the TypeScript compiler as a peer dependency
        # Reference: https://github.com/typescript-language-server/typescript-language-server#installing
        await anyio.run_process(
            ["npm", "install", "-g", "typescript-language-server", "typescript"]
        )
        logger.info("Successfully installed typescript-language-server via npm")
    except CalledProcessError as e:
        raise ServerInstallationError(
            "Could not install typescript-language-server and typescript. Please install them manually with 'npm install -g typescript-language-server typescript'. "
            "See https://github.com/typescript-language-server/typescript-language-server for more information."
        ) from e
    else:
        return


TypescriptLocalServer = partial(
    LocalServer,
    program="typescript-language-server",
    args=["--stdio"],
    ensure_installed=ensure_typescript_installed,
)


@define
class TypescriptClient(
    TypeScriptClientBase,
    WithNotifyDidChangeConfiguration,
    WithRequestCodeAction,
    WithRequestCompletion,
    WithRequestHover,
    WithRequestDefinition,
    WithRequestReferences,
    WithRequestImplementation,
    WithRequestTypeDefinition,
    WithRequestDocumentSymbol,
    WithRequestInlayHint,
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
):
    """
    - Language: TypeScript, JavaScript
    - Homepage: https://github.com/typescript-language-server/typescript-language-server
    - Doc: https://github.com/typescript-language-server/typescript-language-server#readme
    - Github: https://github.com/typescript-language-server/typescript-language-server
    - VSCode Extension: Built-in TypeScript support in VS Code
    """

    @classmethod
    @override
    def create_default_servers(cls) -> DefaultServers:
        return DefaultServers(
            local=TypescriptLocalServer(),
            container=TypescriptContainerServer(),
        )

    @override
    def check_server_compatibility(self, info: lsp_type.ServerInfo | None) -> None:
        return

    @override
    def create_default_config(self) -> dict[str, Any] | None:
        """
        https://github.com/typescript-language-server/typescript-language-server/blob/master/docs/configuration.md
        """
        return {
            "typescript": {
                "inlayHints": {
                    "includeInlayParameterNameHints": "all",
                    "includeInlayParameterNameHintsWhenArgumentMatchesName": True,
                    "includeInlayFunctionParameterTypeHints": True,
                    "includeInlayVariableTypeHints": True,
                    "includeInlayVariableTypeHintsWhenTypeMatchesName": True,
                    "includeInlayPropertyDeclarationTypeHints": True,
                    "includeInlayFunctionLikeReturnTypeHints": True,
                    "includeInlayEnumMemberValueHints": True,
                },
                "suggest": {
                    "autoImports": True,
                    "completeFunctionCalls": True,
                    "includeCompletionsForModuleExports": True,
                },
                "preferences": {
                    "includePackageJsonAutoImports": "on",
                    "importModuleSpecifier": "shortest",
                },
            },
            "javascript": {
                "inlayHints": {
                    "includeInlayParameterNameHints": "all",
                    "includeInlayParameterNameHintsWhenArgumentMatchesName": True,
                    "includeInlayFunctionParameterTypeHints": True,
                    "includeInlayVariableTypeHints": True,
                    "includeInlayVariableTypeHintsWhenTypeMatchesName": True,
                    "includeInlayPropertyDeclarationTypeHints": True,
                    "includeInlayFunctionLikeReturnTypeHints": True,
                    "includeInlayEnumMemberValueHints": True,
                },
                "suggest": {
                    "autoImports": True,
                    "completeFunctionCalls": True,
                    "includeCompletionsForModuleExports": True,
                },
                "preferences": {
                    "includePackageJsonAutoImports": "on",
                    "importModuleSpecifier": "shortest",
                },
            },
        }
