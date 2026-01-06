from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from lsp_client.capability.notification.did_create_files import WithNotifyDidCreateFiles
from lsp_client.capability.notification.did_delete_files import WithNotifyDidDeleteFiles
from lsp_client.capability.notification.did_rename_files import WithNotifyDidRenameFiles
from lsp_client.capability.request.will_create_files import WithRequestWillCreateFiles
from lsp_client.capability.request.will_delete_files import WithRequestWillDeleteFiles
from lsp_client.capability.request.will_rename_files import WithRequestWillRenameFiles
from lsp_client.client.abc import Client
from lsp_client.server import DefaultServers
from lsp_client.utils.types import lsp_type


class WorkspaceFileOpClient(
    Client,
    WithNotifyDidCreateFiles,
    WithNotifyDidRenameFiles,
    WithNotifyDidDeleteFiles,
    WithRequestWillCreateFiles,
    WithRequestWillRenameFiles,
    WithRequestWillDeleteFiles,
):
    @classmethod
    def create_default_servers(cls):
        from unittest.mock import create_autospec

        from lsp_client.server.container import ContainerServer
        from lsp_client.server.local import LocalServer

        return DefaultServers(
            local=create_autospec(LocalServer, instance=True),
            container=create_autospec(ContainerServer, instance=True),
        )

    @classmethod
    def get_language_config(cls):
        from lsp_client.protocol.lang import LanguageConfig

        return LanguageConfig(
            kind=lsp_type.LanguageKind.Python, suffixes=[".py"], project_files=[]
        )

    def check_server_compatibility(self, info):
        pass


@pytest.mark.asyncio
async def test_workspace_file_operations_integration():
    # Mock server behavior
    mock_server = AsyncMock()
    mock_server.wait_requests_completed = AsyncMock()

    # Initialize response
    _ = lsp_type.InitializeResult(
        capabilities=lsp_type.ServerCapabilities(
            workspace=lsp_type.WorkspaceOptions(
                file_operations=lsp_type.FileOperationOptions(
                    will_create=lsp_type.FileOperationRegistrationOptions(filters=[]),
                    did_create=lsp_type.FileOperationRegistrationOptions(filters=[]),
                )
            )
        )
    )

    mock_server.request.side_effect = [
        # Response for initialize
        {
            "jsonrpc": "2.0",
            "id": "initialize",
            "result": {
                "capabilities": {
                    "textDocumentSync": 1,
                    "workspace": {
                        "fileOperations": {
                            "willCreate": {"filters": []},
                            "didCreate": {"filters": []},
                        }
                    },
                }
            },
        },
        # Response for willCreateFiles
        {"jsonrpc": "2.0", "id": "1", "result": None},
        # Response for shutdown
        {"jsonrpc": "2.0", "id": "shutdown", "result": None},
    ]

    with patch("lsp_client.client.abc.Client.run_server") as mock_run:
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def mock_run_server():
            import anyio

            s, r = anyio.create_memory_object_stream(128)
            try:
                yield mock_server, r
            finally:
                s.close()

        mock_run.side_effect = mock_run_server

        async with WorkspaceFileOpClient(workspace=Path.cwd()) as client:
            # Test willCreateFiles
            uris = ["file:///test.py"]
            await client.request_will_create_files(uris)

            # Test didCreateFiles
            await client.notify_did_create_files(uris)

    # Verify initialize was called with correct capabilities
    init_call = mock_server.request.call_args_list[0][0][0]
    assert init_call["method"] == "initialize"
    caps = init_call["params"]["capabilities"]["workspace"]["fileOperations"]
    assert caps["willCreate"] is True
    assert caps["didCreate"] is True
    assert caps["willRename"] is True
    assert caps["didRename"] is True
    assert caps["willDelete"] is True
    assert caps["didDelete"] is True

    # Verify willCreateFiles request
    will_create_call = mock_server.request.call_args_list[1][0][0]
    assert will_create_call["method"] == "workspace/willCreateFiles"
    assert will_create_call["params"]["files"][0]["uri"] == uris[0]

    # Verify didCreateFiles notification
    # index 0 is 'initialized', index 1 is 'workspace/didCreateFiles'
    did_create_call = mock_server.notify.call_args_list[1][0][0]
    assert did_create_call["method"] == "workspace/didCreateFiles"
    assert did_create_call["params"]["files"][0]["uri"] == uris[0]
