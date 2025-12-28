# Language Configuration Guide

In the `lsp-client` SDK, language-specific configurations are primarily defined through the `LanguageConfig` class. This configuration determines how the client identifies files of a specific language, locates project roots, and interacts with the Language Server.

## LanguageConfig

`LanguageConfig` is an immutable configuration class defined in `lsp_client.client.lang`. it contains the following core fields:

- **kind (`lsp_type.LanguageKind`)**:
  Specifies the type of programming language (e.g., `Python`, `Rust`, `Go`, `TypeScript`). This typically corresponds to the language identifier in the LSP protocol.
- **suffixes (`list[str]`)**:
  A list of file extensions associated with the language (e.g., `[".py", ".pyi"]`). The client uses these suffixes to determine if a file belongs to this language.
- **project_files (`list[str]`)**:
  A list of "marker" files used to identify the project root directory (e.g., `["pyproject.toml", "Cargo.toml", "package.json"]`). When the client attempts to determine the root directory for a file, it searches upwards recursively for directories containing these files.
- **exclude_files (`list[str]`)**:
  A list of marker files indicating that a directory should _not_ be considered a project root. For example, `["venv", ".venv"]` can be used to prevent the client from treating a virtual environment as a project root.

## Project Root Discovery

The client determines the project root by searching upwards from the given file path until a valid project root is found or the system root is reached. This discovery is based on the `project_files` and `exclude_files` defined in the `LanguageConfig`.

The `LanguageConfig` class provides a `find_project_root(path: Path)` method:
1. If the path is a file, it first checks if the file suffix matches. If not, it returns `None`.
2. It then searches upwards for `exclude_files`. If found, it stops and returns `None`.
3. It searches upwards for `project_files`. If found, it returns the containing directory.
4. If no markers are found, it returns the original directory (or the file's parent).

## Client Language Attributes

The `Client` base class includes several general configurations related to language processing and server interaction:

- **`sync_file` (bool, default `True`)**:
  Whether to automatically synchronize file content with the server. If enabled, the client automatically sends `textDocument/didOpen` and `textDocument/didClose` notifications when using the `open_files` context manager.
- **`initialization_options` (dict)**:
  Custom options passed to the server during the `initialize` request. Most Language Servers require specific configurations here to function correctly.
- **`request_timeout` (float, default `5.0`)**:
  The timeout in seconds for LSP requests.
- **`create_default_config()`**:
  An optional method to provide default LSP configuration (settings) for the client. These settings are typically used to configure the Language Server's behavior (e.g., enabling/disabling specific analysis features).

## Example: Defining a Custom Language Client

To support a new language, you typically inherit from `Client` and implement the required abstract methods:

```python
from typing import Any, override
from lsp_client.client.abc import Client
from lsp_client.client.lang import LanguageConfig
from lsp_client.server import DefaultServers
from lsp_client.utils.types import lsp_type

class MyNewLanguageClient(Client):
    @classmethod
    @override
    def get_language_config(cls) -> LanguageConfig:
        return LanguageConfig(
            kind=lsp_type.LanguageKind.PlainText,
            suffixes=[".mylang"],
            project_files=["my_project.config"],
            exclude_files=[".ignore_me"]
        )

    @override
    def create_default_servers(self) -> DefaultServers:
        # Define how to start the server (local or containerized)
        ...

    @override
    def check_server_compatibility(self, info: lsp_type.ServerInfo | None) -> None:
        # Optionally check if the server version/info is compatible
        pass

    @override
    def create_default_config(self) -> dict[str, Any] | None:
        # Provide default LSP settings
        return {
            "mylang": {
                "analysis": {
                    "enableFeatureX": True
                }
            }
        }
```
