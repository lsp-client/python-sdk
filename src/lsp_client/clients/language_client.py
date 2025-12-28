from __future__ import annotations

from typing import TYPE_CHECKING, Literal, override

from attrs import define

from lsp_client.client.abc import Client

if TYPE_CHECKING:
    from lsp_client.client.lang import LanguageConfig
    from lsp_client.server import DefaultServers
    from lsp_client.utils.types import lsp_type


Language = Literal["python", "rust", "go", "typescript", "deno"]


@define(kw_only=True)
class LanguageClient(Client):
    language: Language

    def _get_delegate(self) -> Client:
        from .deno import DenoClient
        from .gopls import GoplsClient
        from .pyright import PyrightClient
        from .rust_analyzer import RustAnalyzerClient
        from .typescript import TypescriptClient

        match self.language:
            case "python":
                cls = PyrightClient
            case "rust":
                cls = RustAnalyzerClient
            case "go":
                cls = GoplsClient
            case "typescript":
                cls = TypescriptClient
            case "deno":
                cls = DenoClient
            case _:
                raise ValueError(f"Unsupported language: {self.language}")

        return cls(
            server=self._server_arg,
            workspace=self._workspace_arg,
            sync_file=self.sync_file,
            request_timeout=self.request_timeout,
            initialization_options=self.initialization_options,
        )

    @override
    def get_language_config(self) -> LanguageConfig:
        return self._get_delegate().get_language_config()

    @override
    def create_default_servers(self) -> DefaultServers:
        return self._get_delegate().create_default_servers()

    @override
    def check_server_compatibility(self, info: lsp_type.ServerInfo | None) -> None:
        return self._get_delegate().check_server_compatibility(info)
