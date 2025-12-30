# Example: Using Pyrefly LSP server for Python reference finding
#
# This example demonstrates how to use the Pyrefly language server
# to find all references to a symbol in Python code. Pyrefly is a
# Python language server that provides enhanced static analysis.

from __future__ import annotations

import anyio

import lsp_client
from lsp_client import Position, Range
from lsp_client.clients.pyrefly import PyreflyClient

lsp_client.enable_logging()


async def main() -> None:
    # Initialize Pyrefly client with local server
    # if `workspace` not specified, defaults to current working directory
    async with PyreflyClient() as client:
        # Request references to PyreflyClient at line 22, column 20
        refs = await client.request_references(
            file_path="src/lsp_client/clients/pyrefly.py",
            position=Position(21, 19),
            # some requests may support additional options,
            # e.g. this one excludes the declaration itself from results
            include_declaration=False,
        )

        assert refs, "No references found."

        for ref in refs:
            # LSP Server always returns URI instead of file paths
            # So we need to convert it back to file path using `from_uri`
            file_path = client.from_uri(ref.uri)
            print(f"Reference found at {file_path} - Range: {ref.range}")

        # Verify that this example file contains a reference to PyreflyClient
        # This demonstrates the reference finding functionality works correctly
        assert any(
            ref.uri.endswith(__file__)
            and ref.range
            == Range(
                start=Position(12, 15),
                end=Position(12, 28),
            )
            for ref in refs
        )


if __name__ == "__main__":
    anyio.run(main)
