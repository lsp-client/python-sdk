"""
Example demonstrating default configurations for LSP clients.

This example shows how the new default configurations work:
1. All clients automatically have sensible defaults
2. Inlay hints and other features are enabled out of the box
3. Users can still override defaults if needed
"""

from __future__ import annotations

from lsp_client.clients.pyright import PyrightClient
from lsp_client.clients.rust_analyzer import RustAnalyzerClient
from lsp_client.utils.config import ConfigurationMap


def example_using_defaults():
    """Example: Using default configuration (no setup required)"""
    print("Example 1: Using Default Configuration")
    print("-" * 50)

    # Create a client - it automatically has default configuration
    client = PyrightClient()

    # Get the default configuration that was created
    config_map = client.create_default_configuration_map()

    if config_map:
        print("✓ Default configuration is available!")

        # Check what inlay hints are enabled
        inlay_hints = config_map.get(None, "python.analysis.inlayHints")
        print(f"  Inlay hints configuration: {inlay_hints}")

        # Check type checking mode
        type_checking = config_map.get(None, "python.analysis.typeCheckingMode")
        print(f"  Type checking mode: {type_checking}")

        # Check auto-import completions
        auto_imports = config_map.get(None, "python.analysis.autoImportCompletions")
        print(f"  Auto-import completions: {auto_imports}")

    print()


def example_with_custom_override():
    """Example: Overriding default configuration"""
    print("Example 2: Overriding Default Configuration")
    print("-" * 50)

    # Create a client
    client = RustAnalyzerClient()

    # Get defaults - demonstrating that defaults exist
    _ = client.create_default_configuration_map()
    print("✓ Default configuration created")

    # Create custom configuration that overrides some defaults
    custom_config = ConfigurationMap()
    custom_config.update_global(
        {
            "rust-analyzer": {
                "inlayHints": {
                    "enable": False,  # Disable inlay hints
                },
                "checkOnSave": {"enable": False},  # Disable check on save
            }
        }
    )

    print("✓ Custom configuration created")
    print("  - Inlay hints: disabled")
    print("  - Check on save: disabled")

    # You would set this on the client:
    # client.configuration_map = custom_config

    print()


def example_inspecting_defaults():
    """Example: Inspecting default configurations for all clients"""
    print("Example 3: Inspecting Default Configurations")
    print("-" * 50)

    from lsp_client.clients import clients

    for client_cls in clients:
        client = client_cls()
        config_map = client.create_default_configuration_map()

        if config_map and config_map.has_global_config():
            print(f"✓ {client_cls.__name__} has default configuration")

            # Try to find configuration - inlay hints for most clients,
            # or other features like diagnostics for clients without inlay hints
            for section in [
                "rust-analyzer.inlayHints",
                "gopls.hints",
                "python.analysis.inlayHints",
                "typescript.inlayHints",
                "deno.inlayHints",
                "pyrefly.inlayHints",
                "ty.diagnostics",  # TyClient uses diagnostics instead of inlay hints
            ]:
                value = config_map.get(None, section)
                if value is not None:
                    print(f"  → {section} is configured")
                    break

    print()


if __name__ == "__main__":
    print("LSP Client Default Configuration Examples")
    print("=" * 50)
    print()

    example_using_defaults()
    example_with_custom_override()
    example_inspecting_defaults()

    print("=" * 50)
    print("All examples completed successfully!")
