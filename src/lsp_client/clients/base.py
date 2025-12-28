from __future__ import annotations

from abc import ABC
from typing import override

from lsp_client.client.abc import Client
from lsp_client.client.lang import LanguageConfig
from lsp_client.utils.types import lsp_type


class PythonClientBase(Client, ABC):
    @override
    @classmethod
    def get_language_config(cls) -> LanguageConfig:
        return LanguageConfig(
            kind=lsp_type.LanguageKind.Python,
            suffixes=[".py", ".pyi"],
            project_files=[
                "pyproject.toml",
                "setup.py",
                "setup.cfg",
                "requirements.txt",
                ".python-version",
            ],
        )


class RustClientBase(Client, ABC):
    @override
    @classmethod
    def get_language_config(cls) -> LanguageConfig:
        return LanguageConfig(
            kind=lsp_type.LanguageKind.Rust,
            suffixes=[".rs"],
            project_files=["Cargo.toml"],
        )


class GoClientBase(Client, ABC):
    @override
    @classmethod
    def get_language_config(cls) -> LanguageConfig:
        return LanguageConfig(
            kind=lsp_type.LanguageKind.Go,
            suffixes=[".go"],
            project_files=["go.mod"],
        )


class TypeScriptClientBase(Client, ABC):
    @override
    @classmethod
    def get_language_config(cls) -> LanguageConfig:
        return LanguageConfig(
            kind=lsp_type.LanguageKind.TypeScript,
            suffixes=[".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"],
            project_files=["package.json", "tsconfig.json", "jsconfig.json"],
        )
