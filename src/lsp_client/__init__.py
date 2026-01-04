"""Full-featured, well-typed, and easy-to-use LSP client library.

This package provides a comprehensive implementation of the Language Server Protocol (LSP)
for building Python clients and servers. It offers:

- **LSPClient**: Abstract base class for implementing LSP clients
- **LSPServer**: Abstract base class for implementing LSP servers
- **Capability-based protocol**: Clean separation of LSP capabilities
- **Type-safe implementation**: Full type annotations using lsprotocol
- **Async/await support**: Modern Python async patterns
- **Multiple server backends**: Docker, local process, and custom implementations

Example:
    ```python
    import anyio
    from lsp_client import PyreflyClient, Position

    async def main():
        async with PyreflyClient() as client:
            refs = await client.request_references(
                file_path="src/main.py",
                position=Position(21, 19),
                include_declaration=False,
            )
            for ref in refs:
                print(f"Reference found at {ref.uri} - Range: {ref.range}")

    anyio.run(main)
    ```

For more examples, see the `examples/` directory in the repository.
"""

from __future__ import annotations

from loguru import logger

from .client.abc import Client
from .clients import (
    BasedpyrightClient,
    DenoClient,
    GoplsClient,
    PyreflyClient,
    PyrightClient,
    RustAnalyzerClient,
    TyClient,
    TypescriptClient,
)
from .server.abc import Server, StreamServer
from .server.container import ContainerServer
from .server.local import LocalServer
from .utils.types import *  # noqa: F403

logger.disable(__name__)


def enable_logging() -> None:
    logger.enable(__name__)


def disable_logging() -> None:
    logger.disable(__name__)


# pdoc configuration
__docformat__ = "google"
__pdoc__ = {
    "logger": False,
}

__all__ = [
    "BasedpyrightClient",
    "Client",
    "ContainerServer",
    "DenoClient",
    "GoplsClient",
    "LocalServer",
    "PyreflyClient",
    "PyrightClient",
    "RustAnalyzerClient",
    "Server",
    "StreamServer",
    "TyClient",
    "TypescriptClient",
    "disable_logging",
    "enable_logging",
]
