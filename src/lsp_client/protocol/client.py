"""LSP client protocol defining the minimal interface for LSP operations.

Provides the CapabilityClientProtocol that defines required methods for
workspace management, configuration access, file operations, and LSP message handling.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Protocol, runtime_checkable

import anyio

from lsp_client.utils.config import ConfigurationMap
from lsp_client.utils.types import AnyPath, Notification, Request, Response
from lsp_client.utils.uri import from_local_uri
from lsp_client.utils.workspace import DEFAULT_WORKSPACE_DIR, Workspace

from .lang import LanguageConfig


@runtime_checkable
class CapabilityClientProtocol(Protocol):
    """
    Minimal interface for a client to perform LSP operations.
    """

    @abstractmethod
    def get_workspace(self) -> Workspace:
        """The workspace folders of the client."""

    @abstractmethod
    def get_config_map(self) -> ConfigurationMap:
        """Get the configuration map of the client."""

    @classmethod
    @abstractmethod
    def get_language_config(cls) -> LanguageConfig:
        """Get language-specific configuration for this client."""

    @abstractmethod
    @asynccontextmanager
    def open_files(self, *file_paths: AnyPath) -> AsyncGenerator[None]:
        """Open files in the client.

        Args:
            file_paths (Sequence[AnyPath]): The file paths to open.
        """

    @abstractmethod
    async def request[R](self, req: Request, schema: type[Response[R]]) -> R: ...

    @abstractmethod
    async def notify(self, msg: Notification) -> None: ...

    def as_uri(self, file_path: AnyPath) -> str:
        """
        Turn a file path into a URI.

        For multi-root workspace, using the first part of a relative path as the workspace folder name.
        """

        file_path = Path(file_path)

        if file_path.is_absolute():
            # abs path must be in one of the workspace folders
            if not any(
                file_path.is_relative_to(folder.path)
                for folder in self.get_workspace().values()
            ):
                raise ValueError(f"{file_path} is not a valid workspace file path")

            return file_path.as_uri()

        if len(self.get_workspace()) == 1:  # single root workspace
            folder = self.get_workspace()[DEFAULT_WORKSPACE_DIR]
        else:  # multi-root workspace
            if (root := file_path.parts[0]) not in self.get_workspace():
                raise ValueError(f"{root} is not a valid workspace folder")
            folder = self.get_workspace()[root]

        return (folder.path / file_path).as_uri()

    def from_uri(self, uri: str) -> Path:
        """Convert a URI to an absolute path."""
        return from_local_uri(uri)

    async def read_file(self, file_path: AnyPath) -> str:
        """Read the content of a file in the workspace."""

        uri = self.as_uri(file_path)
        abs_file_path = self.from_uri(uri)
        return await anyio.Path(abs_file_path).read_text()
