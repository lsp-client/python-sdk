from __future__ import annotations

from pathlib import Path

import pytest

from lsp_client.client.abc import Client


@pytest.fixture
def lsp_client(client_cls: type[Client]):
    """Create a client instance for testing."""
    return client_cls()


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace directory."""
    return tmp_path


# Protocol fixtures


@pytest.fixture
def raw_request():
    """Create a sample raw JSON-RPC request."""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "processId": None,
            "capabilities": {},
        },
    }


@pytest.fixture
def raw_notification():
    """Create a sample raw JSON-RPC notification."""
    return {
        "jsonrpc": "2.0",
        "method": "initialized",
        "params": {},
    }


@pytest.fixture
def raw_response():
    """Create a sample raw JSON-RPC response."""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {"capabilities": {}},
    }


# Capability fixtures


@pytest.fixture
def client_capabilities():
    """Create sample client capabilities."""
    from lsp_client.utils.types import lsp_type

    return lsp_type.ClientCapabilities()


@pytest.fixture
def server_capabilities():
    """Create sample server capabilities."""
    from lsp_client.utils.types import lsp_type

    return lsp_type.ServerCapabilities()


# Workspace fixtures


@pytest.fixture
def sample_python_file(temp_workspace):
    """Create a sample Python file for testing."""
    content = '''"""Sample Python module for testing."""


def hello(name: str) -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"


class Greeter:
    """A greeter class."""

    def __init__(self, prefix: str = "Hello"):
        self.prefix = prefix

    def greet(self, name: str) -> str:
        """Greet someone with the prefix."""
        return f"{self.prefix}, {name}!"
'''
    path = temp_workspace / "sample.py"
    path.write_text(content)
    return path


@pytest.fixture
def sample_workspace(temp_workspace, sample_python_file):
    """Create a sample workspace with files for testing."""
    return temp_workspace


# Error fixtures


@pytest.fixture
def json_rpc_error():
    """Create a sample JSON-RPC error response."""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "error": {
            "code": -32600,
            "message": "Invalid Request",
        },
    }


# Configuration fixtures


@pytest.fixture
def default_config():
    """Get default configuration for a client."""
    from lsp_client.utils.types import lsp_type

    return lsp_type.InitializeParams(
        capabilities=lsp_type.ClientCapabilities(),
        process_id=None,
        client_info=lsp_type.ClientInfo(name="test-client", version="0.1.0"),
        locale="en-us",
        root_path=None,
        root_uri=None,
        initialization_options={},
        trace=lsp_type.TraceValue.Off,
        workspace_folders=[],
    )


# Markers for test categorization


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark as a unit test")
    config.addinivalue_line("markers", "integration: mark as an integration test")
    config.addinivalue_line("markers", "e2e: mark as an end-to-end test")
    config.addinivalue_line("markers", "regression: mark as a regression test")
    config.addinivalue_line("markers", "performance: mark as a performance test")
    config.addinivalue_line("markers", "slow: mark as a slow-running test")
    config.addinivalue_line(
        "markers", "requires_server: mark as requiring server installation"
    )
    config.addinivalue_line(
        "markers", "requires_fixtures: mark as requiring pyrefly fixtures"
    )


# Fixture availability checks


@pytest.fixture(scope="session")
def pyrefly_fixtures_available() -> bool:
    """Check if pyrefly fixtures are available."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    pyrefly_dir = fixtures_dir / "pyrefly"
    pyrefly_lsp_dir = fixtures_dir / "pyrefly_lsp"

    return (
        pyrefly_dir.exists()
        and pyrefly_dir.is_dir()
        and pyrefly_lsp_dir.exists()
        and pyrefly_lsp_dir.is_dir()
    )


def pytest_runtest_setup(item):
    """Skip tests that require fixtures if they are not available."""
    if "requires_fixtures" in [mark.name for mark in item.iter_markers()]:
        fixtures_dir = Path(__file__).parent / "fixtures"
        pyrefly_dir = fixtures_dir / "pyrefly"
        pyrefly_lsp_dir = fixtures_dir / "pyrefly_lsp"

        if not (
            pyrefly_dir.exists()
            and pyrefly_dir.is_dir()
            and pyrefly_lsp_dir.exists()
            and pyrefly_lsp_dir.is_dir()
        ):
            pytest.skip("Pyrefly fixtures not available")
