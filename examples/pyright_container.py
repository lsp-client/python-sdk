# Example: Using Pyright LSP server in Docker for Python definition lookup
#
# This example demonstrates how to use Pyright (Microsoft's Python language server)
# running in a Docker container to find definition locations of Python symbols.
# The Docker approach provides isolation and consistent environment setup.

from __future__ import annotations

from pathlib import Path

import anyio

from lsp_client import Position
from lsp_client.clients.pyright import PyrightClient, PyrightContainerServer


async def main() -> None:
    # Set up workspace directory and mount it in Docker
    workspace = Path.cwd()
    async with PyrightClient(
        workspace=workspace,
        # here we use the containerized Pyright server
        server=PyrightContainerServer(),
    ) as client:
        # Find definition of PyrightContainerServer at line 12, column 28
        refs = await client.request_definition_locations(
            file_path=__file__,
            position=Position(12, 28),
        )

        if not refs:
            print("No definition locations found.")
            return

        # Display all definition locations found
        for ref in refs:
            print(f"Definition location found at {ref.uri} - Range: {ref.range}")


if __name__ == "__main__":
    anyio.run(main)  # Run the async example
