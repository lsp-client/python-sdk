from __future__ import annotations

from pathlib import Path
from typing import override

import anyio
import asyncer
import pytest
from lsprotocol.types import LanguageKind

from lsp_client.client.abc import Client
from lsp_client.protocol.lang import LanguageConfig
from lsp_client.server import DefaultServers
from lsp_client.utils.types import AnyPath, lsp_type


class OpenFilesTestClient(Client):
    """Client for testing open_files logic without a real server."""

    @classmethod
    def create_default_servers(cls) -> DefaultServers:
        return None  # type: ignore[return-value]

    @classmethod
    def get_language_config(cls) -> LanguageConfig:
        return LanguageConfig(
            kind=LanguageKind.Python, suffixes=[".py"], project_files=["pyproject.toml"]
        )

    def check_server_compatibility(self, info: lsp_type.ServerInfo | None) -> None:
        pass

    @override
    async def notify_text_document_opened(
        self, file_path: AnyPath, file_content: str
    ) -> None:
        pass

    @override
    async def notify_text_document_closed(self, file_path: AnyPath) -> None:
        pass


@pytest.mark.anyio
async def test_open_files_nested_same_file(tmp_path: Path):
    """Test that nesting open_files for the same file works correctly."""
    file_path = tmp_path / "test.py"
    file_path.write_text("print('hello')")

    client = OpenFilesTestClient(workspace=tmp_path)
    # Mock as_uri to use absolute paths correctly
    client.as_uri = lambda p: Path(p).absolute().as_uri()  # type: ignore[method-assign]
    uri = client.as_uri(file_path)

    async with client.open_files(file_path):
        assert uri in client.document_state._states
        assert client._buffer._ref_count[uri] == 1

        async with client.open_files(file_path):
            assert client._buffer._ref_count[uri] == 2
            # Should still be registered (not registered again)
            assert uri in client.document_state._states

        # After nested close, ref count should be 1 and still registered
        assert client._buffer._ref_count[uri] == 1
        assert uri in client.document_state._states

    # After all closed, should be fully cleaned up
    assert client._buffer._ref_count[uri] == 0
    assert uri not in client.document_state._states


@pytest.mark.anyio
async def test_open_files_concurrent_same_file(tmp_path: Path):
    """Test that concurrent open_files for the same file doesn't cause registration errors."""
    file_path = tmp_path / "test.py"
    file_path.write_text("content")

    client = OpenFilesTestClient(workspace=tmp_path)
    client.as_uri = lambda p: Path(p).absolute().as_uri()  # type: ignore[method-assign]
    uri = client.as_uri(file_path)

    async def worker():
        async with client.open_files(file_path):
            assert uri in client.document_state._states
            await anyio.sleep(0.05)
            assert uri in client.document_state._states

    async with asyncer.create_task_group() as tg:
        for _ in range(5):
            tg.soonify(worker)()

    assert client._buffer._ref_count[uri] == 0
    assert uri not in client.document_state._states


@pytest.mark.anyio
async def test_open_files_mixed_files(tmp_path: Path):
    """Test opening multiple files in different combinations."""
    f1 = tmp_path / "f1.py"
    f2 = tmp_path / "f2.py"
    f1.write_text("1")
    f2.write_text("2")

    client = OpenFilesTestClient(workspace=tmp_path)
    client.as_uri = lambda p: Path(p).absolute().as_uri()  # type: ignore[method-assign]
    u1, u2 = client.as_uri(f1), client.as_uri(f2)

    async with client.open_files(f1):
        assert u1 in client.document_state._states
        async with client.open_files(f1, f2):
            assert client._buffer._ref_count[u1] == 2
            assert client._buffer._ref_count[u2] == 1
            assert u2 in client.document_state._states

        assert client._buffer._ref_count[u1] == 1
        assert u2 not in client.document_state._states

    assert u1 not in client.document_state._states
