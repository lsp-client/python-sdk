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
    WithNotifyDidCreateFiles,
    WithNotifyDidDeleteFiles,
    WithNotifyDidRenameFiles,
)
from lsp_client.capability.request import (
    WithDocumentDiagnostic,
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
from lsp_client.clients.base import RustClientBase
from lsp_client.server import DefaultServers, ServerInstallationError
from lsp_client.server.container import ContainerServer
from lsp_client.server.local import LocalServer
from lsp_client.utils.types import lsp_type

RustAnalyzerContainerServer = partial(
    ContainerServer, image="ghcr.io/lsp-client/rust-analyzer:latest"
)


async def ensure_rust_analyzer_installed() -> None:
    if shutil.which("rust-analyzer"):
        return

    logger.warning("rust-analyzer not found, attempting to install...")

    try:
        await anyio.run_process(["rustup", "component", "add", "rust-analyzer"])
        logger.info("Successfully installed rust-analyzer via rustup")
    except CalledProcessError as e:
        raise ServerInstallationError(
            "Could not install rust-analyzer. Please install it manually with 'rustup component add rust-analyzer'. "
            "See https://rust-analyzer.github.io/ for more information."
        ) from e


RustAnalyzerLocalServer = partial(
    LocalServer,
    program="rust-analyzer",
    args=[],
    ensure_installed=ensure_rust_analyzer_installed,
)


@define
class RustAnalyzerClient(
    RustClientBase,
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
    WithRequestImplementation,
    WithRequestInlayHint,
    WithDocumentDiagnostic,
    WithRequestReferences,
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
    - Language: Rust
    - Homepage: https://rust-analyzer.github.io/
    - Doc: https://rust-analyzer.github.io/manual.html
    - Github: https://github.com/rust-lang/rust-analyzer
    - VSCode Extension: https://marketplace.visualstudio.com/items?itemName=rust-lang.rust-analyzer
    """

    @classmethod
    @override
    def create_default_servers(cls) -> DefaultServers:
        return DefaultServers(
            local=RustAnalyzerLocalServer(),
            container=RustAnalyzerContainerServer(),
        )

    @override
    def check_server_compatibility(self, info: lsp_type.ServerInfo | None) -> None:
        return

    @override
    def create_default_config(self) -> dict[str, Any] | None:
        """
        https://rust-analyzer.github.io/book/configuration.html
        """
        return {
            "rust-analyzer": {
                "cargo": {
                    "buildScripts": {"enable": True},
                    "features": "all",
                },
                "checkOnSave": {"enable": True},
                "completion": {
                    "autoimport": {"enable": True},
                    "callable": {"snippets": "fill_arguments"},
                    "postfix": {"enable": True},
                },
                "diagnostics": {
                    "enable": True,
                    "experimental": {"enable": True},
                },
                "hover": {
                    "actions": {
                        "enable": True,
                        "references": {"enable": True},
                    }
                },
                "inlayHints": {
                    "enable": True,
                    "bindingModeHints": {"enable": True},
                    "closureCaptureHints": {"enable": True},
                    "chainingHints": {"enable": True},
                    "closureReturnTypeHints": {"enable": "always"},
                    "lifetimeElisionHints": {"enable": "always"},
                    "discriminantHints": {"enable": "always"},
                    "expressionAdjustmentHints": {"enable": "always"},
                    "parameterHints": {"enable": True},
                    "reborrowHints": {"enable": "always"},
                    "typeHints": {"enable": True},
                },
            }
        }
