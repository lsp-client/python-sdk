from __future__ import annotations

import pytest

from lsp_client.capability.server_request import WithRespondConfigurationRequest
from lsp_client.clients import clients
from lsp_client.utils.config import ConfigurationMap


@pytest.mark.parametrize("client_cls", clients)
def test_clients_have_default_configuration_method(client_cls):
    """Test that all clients have a create_default_configuration_map method."""
    assert hasattr(client_cls, "create_default_configuration_map"), (
        f"{client_cls.__name__} should have create_default_configuration_map method"
    )


@pytest.mark.parametrize("client_cls", clients)
def test_default_configuration_returns_valid_type(client_cls):
    """Test that create_default_configuration_map returns None or ConfigurationMap."""
    client = client_cls()
    result = client.create_default_configuration_map()
    assert result is None or isinstance(result, ConfigurationMap), (
        f"{client_cls.__name__}.create_default_configuration_map() should return None or ConfigurationMap"
    )


@pytest.mark.parametrize("client_cls", clients)
def test_clients_with_configuration_support_have_defaults(client_cls):
    """Test that clients supporting configuration have default configuration maps."""
    client = client_cls()

    # Check if client supports configuration request
    if not isinstance(client, WithRespondConfigurationRequest):
        pytest.skip(
            f"{client_cls.__name__} does not support WithRespondConfigurationRequest"
        )

    # Get default configuration
    config_map = client.create_default_configuration_map()

    # Clients with configuration support should have defaults
    # (especially those with inlay hints, diagnostics, etc.)
    assert config_map is not None, (
        f"{client_cls.__name__} supports configuration requests "
        f"and should provide default configuration"
    )

    # Verify it's a proper ConfigurationMap instance
    assert isinstance(config_map, ConfigurationMap)


@pytest.mark.parametrize("client_cls", clients)
def test_default_configuration_has_content(client_cls):
    """Test that default configurations contain actual settings."""
    client = client_cls()
    config_map = client.create_default_configuration_map()

    if config_map is None:
        pytest.skip(f"{client_cls.__name__} has no default configuration")

    # Check that the configuration map has some content using public API
    assert config_map.has_global_config(), (
        f"{client_cls.__name__} default configuration should not be empty"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("client_cls", clients)
async def test_configuration_initialized_on_client_startup(client_cls):
    """Test that configuration is automatically initialized when client starts."""
    # This test would require actually starting the language server
    # For now, we just verify the client can be instantiated
    client = client_cls()

    # Check if client supports configuration
    if isinstance(client, WithRespondConfigurationRequest):
        # Before async context, configuration_map should be None
        assert client.configuration_map is None

    # Note: Full integration test would require:
    # async with client as c:
    #     if isinstance(c, WithRespondConfigurationRequest):
    #         assert c.configuration_map is not None
    # But this requires language servers to be installed


def test_rust_analyzer_default_config_has_inlay_hints():
    """Test that rust-analyzer default config enables inlay hints."""
    from lsp_client.clients.rust_analyzer import RustAnalyzerClient

    client = RustAnalyzerClient()
    config_map = client.create_default_configuration_map()

    assert config_map is not None
    config = config_map.get(None, "rust-analyzer.inlayHints.enable")
    assert config is True, "rust-analyzer should enable inlay hints by default"


def test_gopls_default_config_has_hints():
    """Test that gopls default config enables hints."""
    from lsp_client.clients.gopls import GoplsClient

    client = GoplsClient()
    config_map = client.create_default_configuration_map()

    assert config_map is not None
    config = config_map.get(None, "gopls.hints")
    assert config is not None, "gopls should have hints configuration"
    assert isinstance(config, dict), "gopls hints should be a dict"


def test_pyright_default_config_has_inlay_hints():
    """Test that pyright default config enables inlay hints."""
    from lsp_client.clients.pyright import PyrightClient

    client = PyrightClient()
    config_map = client.create_default_configuration_map()

    assert config_map is not None
    config = config_map.get(None, "python.analysis.inlayHints")
    assert config is not None, "pyright should have inlay hints configuration"
    assert isinstance(config, dict), "pyright inlay hints should be a dict"


def test_typescript_default_config_has_inlay_hints():
    """Test that typescript-language-server default config enables inlay hints."""
    from lsp_client.clients.typescript import TypescriptClient

    client = TypescriptClient()
    config_map = client.create_default_configuration_map()

    assert config_map is not None
    config = config_map.get(None, "typescript.inlayHints")
    assert config is not None, "typescript should have inlay hints configuration"


def test_deno_default_config_has_inlay_hints():
    """Test that deno default config enables inlay hints."""
    from lsp_client.clients.deno import DenoClient

    client = DenoClient()
    config_map = client.create_default_configuration_map()

    assert config_map is not None
    config = config_map.get(None, "deno.inlayHints")
    assert config is not None, "deno should have inlay hints configuration"


def test_pyrefly_default_config_has_inlay_hints():
    """Test that pyrefly default config enables inlay hints."""
    from lsp_client.clients.pyrefly import PyreflyClient

    client = PyreflyClient()
    config_map = client.create_default_configuration_map()

    assert config_map is not None
    config = config_map.get(None, "pyrefly.inlayHints")
    assert config is not None, "pyrefly should have inlay hints configuration"
    assert isinstance(config, dict), "pyrefly inlay hints should be a dict"


def test_ty_default_config_has_diagnostics():
    """Test that ty default config enables diagnostics and completion."""
    from lsp_client.clients.ty import TyClient

    client = TyClient()
    config_map = client.create_default_configuration_map()

    assert config_map is not None
    diagnostics = config_map.get(None, "ty.diagnostics")
    assert diagnostics is not None, "ty should have diagnostics configuration"
    completion = config_map.get(None, "ty.completion")
    assert completion is not None, "ty should have completion configuration"
