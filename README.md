# LSP Client

[![PyPI version](https://img.shields.io/pypi/v/lsp-client.svg)](https://pypi.org/project/lsp-client/)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![CI](https://github.com/observerw/lsp-client/actions/workflows/ci.yml/badge.svg)](https://github.com/observerw/lsp-client/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-pdoc-blue)](https://observerw.github.io/lsp-client/)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/observerw/lsp-client)

A production-ready, async-first Python client for the Language Server Protocol (LSP). Built for developers who need fine-grained control, container isolation, and extensibility when integrating language intelligence into their tools.

## Why lsp-client?

`lsp-client` is engineered for developers building **production-grade tooling** that requires precise control over language server environments:

- **🧩 Intelligent Capability Management**: Zero-overhead mixin system with automatic registration, negotiation, and availability checks. Only access methods for registered capabilities.
- **🎨 Ergonomic API Design**: Every capability method is designed for developer productivity. The SDK handles complex LSP response types (like `Location` vs `LocationLink`), providing consistent, high-level Python objects instead of raw JSON-RPC structures.
- **🎯 Universal LSP Support**: Full 3.17 specification coverage. Supports all standard client requests, notifications, and server-to-client interactions. If a capability exists in the LSP spec, you can use or implement it here.
- **🐳 Container-First Architecture**: Containers as first-class citizens with workspace mounting, path translation, and lifecycle management. Pre-built images available, seamless switching between local and container environments.
- **🛡️ Fail-Safe Capability Validation**: Sophisticated pre-flight checks ensure that the server's capabilities perfectly match the client's requirements before the first request is ever sent. Catch configuration mismatches at startup rather than during runtime.
- **⚡ Production-Ready & Modern**: Explicit environment control with no auto-downloads. Built with async patterns, comprehensive error handling, retries, and full type safety.

## Quick Start

### Installation

```bash
uv add lsp-client
```

### Local Language Server

The following code snippet can be run as-is, try it out:

```python
# NOTE: install pyrefly with `uv tool install pyrefly` first
import anyio
from lsp_client import Position, PyreflyClient

async def main():
    async with PyreflyClient() as client:
        refs = await client.request_references(
            file_path="example.py",
            position=Position(10, 5)
        )
        for ref in refs:
            print(f"Reference at {ref.uri}: {ref.range}")

anyio.run(main)
```

### Containerized Language Server

```python
import anyio
from pathlib import Path
from lsp_client import Position, PyrightClient
from lsp_client.clients.pyright import PyrightContainerServer

async def main():
    workspace = Path.cwd()
    async with PyrightClient(
        server=PyrightContainerServer(),
        workspace=workspace
    ) as client:
        # Find definition of a symbol
        definitions = await client.request_definition_locations(
            file_path="example.py",
            position=Position(10, 5)
        )
        if definitions:
            for def_loc in definitions:
                print(f"Definition at {def_loc.uri}: {def_loc.range}")

anyio.run(main)
```

### More Examples

The `examples/` directory contains comprehensive usage examples:

- `pyright_container.py` - Using Pyright in Docker for Python analysis
- `rust_analyzer.py` - Rust code intelligence with Rust-Analyzer
- `pyrefly.py` - Python linting and analysis with Pyrefly
- `protocol.py` - Direct LSP protocol usage

Run examples with:

```bash
uv run examples/pyright_container.py
```

## Client Definition

Defining a custom client is super easy with the capability mixin:

```python
@define
class MyPythonClient(
    Client,
    WithRequestHover, # textDocument/hover
    WithRequestDefinition, # textDocument/definition
    WithRequestReferences, # textDocument/references
    WithNotifyDidChangeConfiguration, # workspace/didChangeConfiguration
    # ... and other capabilities as needed
):
    def create_default_servers(self) -> DefaultServers:
        return DefaultServers(
            # support both local ...
            local=LocalServer(program="pylsp", args=["--stdio"]),
            # ... and containerized server!
            container=ContainerServer(image="ghcr.io/observerw/lsp-client/python-lsp-server")
        )

    def create_initialization_options(self) -> dict:
        return {"plugins": {"pyflakes": {"enabled": True}}} # custom init options

    def check_server_compatibility(self, info: lsp_type.ServerInfo | None) -> None:
        return  # Custom compatibility checks if needed
```

## Current Supported Language Servers

| Language Server            | Module Path                        | Language              | Container Image                           |
| -------------------------- | ---------------------------------- | --------------------- | ----------------------------------------- |
| Pyright                    | `lsp_client.clients.pyright`       | Python                | `ghcr.io/lsp-client/pyright:latest`       |
| Basedpyright               | `lsp_client.clients.basedpyright`  | Python                | `ghcr.io/lsp-client/basedpyright:latest`  |
| Pyrefly                    | `lsp_client.clients.pyrefly`       | Python                | `ghcr.io/lsp-client/pyrefly:latest`       |
| Ty                         | `lsp_client.clients.ty`            | Python                | `ghcr.io/lsp-client/ty:latest`            |
| Rust Analyzer              | `lsp_client.clients.rust_analyzer` | Rust                  | `ghcr.io/lsp-client/rust-analyzer:latest` |
| Deno                       | `lsp_client.clients.deno`          | TypeScript/JavaScript | `ghcr.io/lsp-client/deno:latest`          |
| TypeScript Language Server | `lsp_client.clients.typescript`    | TypeScript/JavaScript | `ghcr.io/lsp-client/typescript:latest`    |
| Gopls                      | `lsp_client.clients.gopls`         | Go                    | `ghcr.io/lsp-client/gopls:latest`         |

Container images are automatically updated weekly to ensure access to the latest language server versions.

### Key Benefits

1. **Method Safety**: You can only call methods for capabilities you've registered. No runtime surprises from unavailable capabilities.
2. **Automatic Registration**: The mixin system automatically handles client registration, capability negotiation, and availability checks behind the scenes.
3. **Zero Boilerplate**: No manual capability checking, no complex initialization logic, no error handling for missing capabilities.
4. **Type Safety**: Full type annotations ensure you get compile-time guarantees about available methods.
5. **Composability**: Mix and match exactly the capabilities you need, creating perfectly tailored clients.

## Advanced Features

### Resilient Server Selection

`lsp-client` implements a prioritized server loading strategy to ensure your tool works across different environments without manual configuration:

1. **Explicit Server**: If you provide a specific `Server` instance, it will be used first.
2. **Local Environment**: It checks if the required language server is already installed in the local system path.
3. **Container Fallback**: If no local server is found, it automatically falls back to a containerized version (using Docker), ensuring zero-setup for end users.
4. **Auto-Install**: As a last resort, it can attempt to automatically install the server locally if an installation hook is defined.

### Fine-Grained Capability Control

The mixin-based architecture allows you to define exactly what your client supports. This is not just for organization; it directly affects the `Initialize` request sent to the server, ensuring the server only sends relevant notifications and doesn't waste resources on unused features.

### Transparent Path Translation

When using containerized servers, `lsp-client` automatically handles path translation between your host machine and the container. You work with local paths, and the client ensures the server sees the correct container-relative paths.

### Smart Configuration Management

`lsp-client` features a sophisticated configuration system designed for production use:

- **Sensible Defaults**: Every built-in client comes pre-configured with optimized settings. Features like **inlay hints**, **auto-imports**, and **advanced diagnostics** are enabled out-of-the-box.
- **Hierarchical Overrides**: Use `ConfigurationMap` to manage global settings and path-based overrides (e.g., different linting rules for `tests/` vs `src/`).
- **Deep Merging**: Settings are merged recursively, allowing you to override specific sub-keys without losing the rest of the default configuration.
- **Automatic Sync**: The SDK automatically handles `workspace/didChangeConfiguration` notifications, ensuring the language server always has the latest settings without a restart.

### Highly Customizable Architecture

The library is built with extensibility as a core principle. You are never locked into the default behavior:

- **Capability Overriding**: You can easily customize how the client handles specific LSP requests or notifications by overriding the capability methods. Want to filter diagnostics or transform hover content before it reaches your application? Just override the corresponding method in your custom client.
- **Middleware Support**: Intercept and modify outgoing requests or incoming responses to implement custom logic like caching, logging, or request debouncing.
- **Custom Servers**: Beyond the built-in local and container servers, you can implement your own `Server` class to connect to language servers over custom transports (e.g., WebSockets, named pipes, or remote SSH).

## Contributing

We welcome contributions! Please see our [Contributing Guide](docs/contribution/) for details on:

- Adding new language server support
- Extending protocol capabilities
- Container image updates
- Development workflow

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built on the [Language Server Protocol](https://microsoft.github.io/language-server-protocol/) specification
- Uses [lsprotocol](https://github.com/microsoft/lsprotocol) for LSP type definitions
- Architecture inspired by [multilspy](https://github.com/microsoft/multilspy) and other LSP clients
