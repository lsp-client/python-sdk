# Example: Basic Rust Analyzer LSP client setup
#
# This example demonstrates how to initialize a Rust Analyzer client
# and retrieve basic information about the language server configuration.
# Rust Analyzer is the official language server for Rust programming language.

from __future__ import annotations

import anyio

import lsp_client
from lsp_client.clients.rust_analyzer import RustAnalyzerClient

lsp_client.enable_logging()


async def main() -> None:
    # Initialize Rust Analyzer client with local server
    async with RustAnalyzerClient() as client:
        # Get and display the language ID for this client
        # This should return "rust" for Rust Analyzer
        print(client.get_language_config().kind.value)


if __name__ == "__main__":
    anyio.run(main)  # Run the async example
