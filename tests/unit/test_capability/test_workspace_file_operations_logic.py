from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
from lsprotocol import types as lsp_type

from lsp_client.capability.notification.did_create_files import WithNotifyDidCreateFiles
from lsp_client.capability.notification.did_delete_files import WithNotifyDidDeleteFiles
from lsp_client.capability.notification.did_rename_files import WithNotifyDidRenameFiles
from lsp_client.capability.request.will_create_files import WithRequestWillCreateFiles
from lsp_client.capability.request.will_delete_files import WithRequestWillDeleteFiles
from lsp_client.capability.request.will_rename_files import WithRequestWillRenameFiles


class MockClient:
    def __init__(self):
        self.request_mock = AsyncMock()
        self.notify_mock = AsyncMock()
        self.get_workspace_mock = MagicMock()
        self.get_config_map_mock = MagicMock()
        self._document_state = MagicMock()

    def get_workspace(self):
        return self.get_workspace_mock()

    def get_config_map(self):
        return self.get_config_map_mock()

    @classmethod
    def get_language_config(cls):
        return MagicMock()

    @asynccontextmanager
    async def open_files(self, *file_paths):
        yield

    async def read_file(self, file_path):
        return ""

    async def write_file(self, uri, content):
        pass

    def from_uri(self, uri, *, relative=True):
        return MagicMock()

    async def request(self, req, schema):
        return await self.request_mock(req, schema)

    async def notify(self, msg):
        await self.notify_mock(msg)


@pytest.mark.asyncio
async def test_request_will_create_files():
    class TestClient(MockClient, WithRequestWillCreateFiles):
        pass

    client = TestClient()
    uris = ["file:///test.py"]
    await client.request_will_create_files(uris)

    client.request_mock.assert_called_once()
    call_args = client.request_mock.call_args[0][0]
    assert isinstance(call_args, lsp_type.WillCreateFilesRequest)
    assert call_args.params.files[0].uri == uris[0]


@pytest.mark.asyncio
async def test_request_will_rename_files():
    class TestClient(MockClient, WithRequestWillRenameFiles):
        pass

    client = TestClient()
    renames = [("file:///old.py", "file:///new.py")]
    await client.request_will_rename_files(renames)

    client.request_mock.assert_called_once()
    call_args = client.request_mock.call_args[0][0]
    assert isinstance(call_args, lsp_type.WillRenameFilesRequest)
    assert call_args.params.files[0].old_uri == renames[0][0]
    assert call_args.params.files[0].new_uri == renames[0][1]


@pytest.mark.asyncio
async def test_request_will_delete_files():
    class TestClient(MockClient, WithRequestWillDeleteFiles):
        pass

    client = TestClient()
    uris = ["file:///test.py"]
    await client.request_will_delete_files(uris)

    client.request_mock.assert_called_once()
    call_args = client.request_mock.call_args[0][0]
    assert isinstance(call_args, lsp_type.WillDeleteFilesRequest)
    assert call_args.params.files[0].uri == uris[0]


@pytest.mark.asyncio
async def test_notify_did_create_files():
    class TestClient(MockClient, WithNotifyDidCreateFiles):
        pass

    client = TestClient()
    uris = ["file:///test.py"]
    await client.notify_did_create_files(uris)

    client.notify_mock.assert_called_once()
    call_args = client.notify_mock.call_args[0][0]
    assert isinstance(call_args, lsp_type.DidCreateFilesNotification)
    assert call_args.params.files[0].uri == uris[0]


@pytest.mark.asyncio
async def test_notify_did_rename_files():
    class TestClient(MockClient, WithNotifyDidRenameFiles):
        pass

    client = TestClient()
    renames = [("file:///old.py", "file:///new.py")]
    await client.notify_did_rename_files(renames)

    client.notify_mock.assert_called_once()
    call_args = client.notify_mock.call_args[0][0]
    assert isinstance(call_args, lsp_type.DidRenameFilesNotification)
    assert call_args.params.files[0].old_uri == renames[0][0]
    assert call_args.params.files[0].new_uri == renames[0][1]


@pytest.mark.asyncio
async def test_notify_did_delete_files():
    class TestClient(MockClient, WithNotifyDidDeleteFiles):
        pass

    client = TestClient()
    uris = ["file:///test.py"]
    await client.notify_did_delete_files(uris)

    client.notify_mock.assert_called_once()
    call_args = client.notify_mock.call_args[0][0]
    assert isinstance(call_args, lsp_type.DidDeleteFilesNotification)
    assert call_args.params.files[0].uri == uris[0]
