"""Language-specific configuration for LSP clients.

Provides LanguageConfig for defining language properties including file suffixes,
project markers, and project root detection logic.
"""

from __future__ import annotations

from pathlib import Path

from attrs import Factory, frozen

from lsp_client.utils.workspace import lsp_type


@frozen
class LanguageConfig:
    """Configuration for a programming language in the LSP client."""

    kind: lsp_type.LanguageKind
    """The kind of programming language."""

    suffixes: list[str]
    """File suffixes associated with the language."""

    project_files: list[str]
    """Files that indicate the root of a project for this language."""

    exclude_files: list[str] = Factory(list)
    """Files that indicate a directory should not be considered a project root for this language."""

    def _find_project_root(self, dir_path: Path) -> Path | None:
        for project_path in (dir_path, *dir_path.parents):
            if any((project_path / excl).exists() for excl in self.exclude_files):
                return None
            if any((project_path / proj).exists() for proj in self.project_files):
                return project_path
        return None

    def find_project_root(self, path: Path) -> Path | None:
        if path.is_file():
            if not any(path.name.endswith(suffix) for suffix in self.suffixes):
                return None
            path = path.parent

        return self._find_project_root(path)
