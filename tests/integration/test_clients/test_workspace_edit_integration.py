from __future__ import annotations

import tempfile
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from unittest.mock import MagicMock

import anyio
import pytest
from lsprotocol import types as lsp_type

from lsp_client.capability.server_request.apply_edit import WithRespondApplyEdit
from lsp_client.client.document_state import DocumentStateManager
from lsp_client.protocol.lang import LanguageConfig
from lsp_client.utils.config import ConfigurationMap
from lsp_client.utils.types import AnyPath, Notification, Request, Response
from lsp_client.utils.workspace import Workspace, WorkspaceFolder


class MockLSPClient(WithRespondApplyEdit):
    """Mock LSP client for integration testing."""

    def __init__(self, temp_dir: Path | None = None) -> None:
        self._document_state = DocumentStateManager()
        self._files: dict[str, str] = {}
        self._temp_dir = temp_dir
        self.server = MagicMock()
        workspace_path = temp_dir if temp_dir else Path("/mock/workspace")
        self._workspace = Workspace(
            {".": WorkspaceFolder(name=".", uri=workspace_path.absolute().as_uri())}
        )
        self._config_map = ConfigurationMap({})

    async def read_file(self, file_path: AnyPath) -> str:
        if self._temp_dir:
            path = anyio.Path(file_path)
            if await path.exists():
                return await path.read_text()
            raise FileNotFoundError(f"File not found: {file_path}")

        path_str = str(file_path)
        if path_str not in self._files:
            raise FileNotFoundError(f"File not found: {file_path}")
        return self._files[path_str]

    async def write_file(self, uri: str, content: str) -> None:
        if self._temp_dir:
            path = uri.replace("file://", "")
            await anyio.Path(path).write_text(content)
        else:
            path = uri.replace("file://", "")
            self._files[path] = content

    def from_uri(self, uri: str, *, relative: bool = True) -> Path:
        return Path(uri.replace("file://", ""))

    def get_workspace(self) -> Workspace:
        return self._workspace

    def get_config_map(self) -> ConfigurationMap:
        return self._config_map

    @classmethod
    def get_language_config(cls) -> LanguageConfig:
        return LanguageConfig(
            kind=lsp_type.LanguageKind.Python,
            suffixes=[".py"],
            project_files=["pyproject.toml"],
        )

    async def request[R](self, req: Request, schema: type[Response[R]]) -> R:
        raise NotImplementedError

    async def notify(self, msg: Notification) -> None:
        pass

    @asynccontextmanager
    async def open_files(self, *file_paths: AnyPath) -> AsyncGenerator[None]:
        yield


@pytest.mark.asyncio
async def test_apply_edit_request_success():
    """Test workspace/applyEdit request with successful application."""
    client = MockLSPClient()
    client._files["/test.py"] = "def hello():\n    pass\n"
    client._document_state.register(
        "file:///test.py", "def hello():\n    pass\n", version=0
    )

    request = lsp_type.ApplyWorkspaceEditRequest(
        id="test-1",
        params=lsp_type.ApplyWorkspaceEditParams(
            edit=lsp_type.WorkspaceEdit(
                document_changes=[
                    lsp_type.TextDocumentEdit(
                        text_document=lsp_type.OptionalVersionedTextDocumentIdentifier(
                            uri="file:///test.py", version=0
                        ),
                        edits=[
                            lsp_type.TextEdit(
                                range=lsp_type.Range(
                                    start=lsp_type.Position(line=0, character=4),
                                    end=lsp_type.Position(line=0, character=9),
                                ),
                                new_text="world",
                            )
                        ],
                    )
                ]
            )
        ),
    )

    response = await client.respond_apply_edit(request)
    assert response.result.applied is True
    assert response.result.failure_reason is None
    assert client._files["/test.py"] == "def world():\n    pass\n"
    assert client._document_state.get_version("file:///test.py") == 1


@pytest.mark.asyncio
async def test_apply_edit_request_version_mismatch():
    """Test workspace/applyEdit request with version mismatch."""
    client = MockLSPClient()
    client._files["/test.py"] = "def hello():\n    pass\n"
    client._document_state.register(
        "file:///test.py", "def hello():\n    pass\n", version=5
    )

    request = lsp_type.ApplyWorkspaceEditRequest(
        id="test-2",
        params=lsp_type.ApplyWorkspaceEditParams(
            edit=lsp_type.WorkspaceEdit(
                document_changes=[
                    lsp_type.TextDocumentEdit(
                        text_document=lsp_type.OptionalVersionedTextDocumentIdentifier(
                            uri="file:///test.py", version=0
                        ),
                        edits=[
                            lsp_type.TextEdit(
                                range=lsp_type.Range(
                                    start=lsp_type.Position(line=0, character=4),
                                    end=lsp_type.Position(line=0, character=9),
                                ),
                                new_text="world",
                            )
                        ],
                    )
                ]
            )
        ),
    )

    response = await client.respond_apply_edit(request)
    assert response.result.applied is False
    assert response.result.failure_reason is not None
    assert "Version mismatch" in response.result.failure_reason


@pytest.mark.asyncio
async def test_apply_edit_request_untracked_document():
    """Test workspace/applyEdit request on untracked document."""
    client = MockLSPClient()
    client._files["/test.py"] = "def hello():\n    pass\n"

    request = lsp_type.ApplyWorkspaceEditRequest(
        id="test-3",
        params=lsp_type.ApplyWorkspaceEditParams(
            edit=lsp_type.WorkspaceEdit(
                document_changes=[
                    lsp_type.TextDocumentEdit(
                        text_document=lsp_type.OptionalVersionedTextDocumentIdentifier(
                            uri="file:///test.py", version=0
                        ),
                        edits=[
                            lsp_type.TextEdit(
                                range=lsp_type.Range(
                                    start=lsp_type.Position(line=0, character=4),
                                    end=lsp_type.Position(line=0, character=9),
                                ),
                                new_text="world",
                            )
                        ],
                    )
                ]
            )
        ),
    )

    response = await client.respond_apply_edit(request)
    assert response.result.applied is False
    assert response.result.failure_reason is not None
    assert "not open in client" in response.result.failure_reason


@pytest.mark.asyncio
async def test_apply_edit_increments_version():
    """Test that successful applyEdit increments document version."""
    client = MockLSPClient()
    client._files["/test.py"] = "line 1\nline 2\n"
    client._document_state.register("file:///test.py", "line 1\nline 2\n", version=0)

    assert client._document_state.get_version("file:///test.py") == 0

    request = lsp_type.ApplyWorkspaceEditRequest(
        id="test-4",
        params=lsp_type.ApplyWorkspaceEditParams(
            edit=lsp_type.WorkspaceEdit(
                document_changes=[
                    lsp_type.TextDocumentEdit(
                        text_document=lsp_type.OptionalVersionedTextDocumentIdentifier(
                            uri="file:///test.py", version=0
                        ),
                        edits=[
                            lsp_type.TextEdit(
                                range=lsp_type.Range(
                                    start=lsp_type.Position(line=0, character=0),
                                    end=lsp_type.Position(line=0, character=6),
                                ),
                                new_text="modified",
                            )
                        ],
                    )
                ]
            )
        ),
    )

    await client.respond_apply_edit(request)

    # Version should be incremented to 1
    assert client._document_state.get_version("file:///test.py") == 1
    assert client._document_state.get_content("file:///test.py") == "modified\nline 2\n"


@pytest.mark.asyncio
async def test_multiple_edits_sequential():
    """Test multiple sequential workspace edits with version tracking."""
    client = MockLSPClient()
    client._files["/test.py"] = "version 0\n"
    client._document_state.register("file:///test.py", "version 0\n", version=0)

    # First edit (version 0 -> 1)
    request1 = lsp_type.ApplyWorkspaceEditRequest(
        id="test-5-1",
        params=lsp_type.ApplyWorkspaceEditParams(
            edit=lsp_type.WorkspaceEdit(
                document_changes=[
                    lsp_type.TextDocumentEdit(
                        text_document=lsp_type.OptionalVersionedTextDocumentIdentifier(
                            uri="file:///test.py", version=0
                        ),
                        edits=[
                            lsp_type.TextEdit(
                                range=lsp_type.Range(
                                    start=lsp_type.Position(line=0, character=8),
                                    end=lsp_type.Position(line=0, character=9),
                                ),
                                new_text="1",
                            )
                        ],
                    )
                ]
            )
        ),
    )

    response1 = await client.respond_apply_edit(request1)
    assert response1.result.applied is True
    assert client._document_state.get_version("file:///test.py") == 1
    assert client._document_state.get_content("file:///test.py") == "version 1\n"

    # Second edit (version 1 -> 2)
    request2 = lsp_type.ApplyWorkspaceEditRequest(
        id="test-5-2",
        params=lsp_type.ApplyWorkspaceEditParams(
            edit=lsp_type.WorkspaceEdit(
                document_changes=[
                    lsp_type.TextDocumentEdit(
                        text_document=lsp_type.OptionalVersionedTextDocumentIdentifier(
                            uri="file:///test.py", version=1
                        ),
                        edits=[
                            lsp_type.TextEdit(
                                range=lsp_type.Range(
                                    start=lsp_type.Position(line=0, character=8),
                                    end=lsp_type.Position(line=0, character=9),
                                ),
                                new_text="2",
                            )
                        ],
                    )
                ]
            )
        ),
    )

    response2 = await client.respond_apply_edit(request2)
    assert response2.result.applied is True
    assert client._document_state.get_version("file:///test.py") == 2
    assert client._document_state.get_content("file:///test.py") == "version 2\n"


@pytest.mark.asyncio
async def test_apply_edit_with_resource_operations():
    """Test workspace/applyEdit with resource operations (create, rename, delete)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        client = MockLSPClient(temp_dir=temp_path)

        # Create a file
        test_file = temp_path / "test.py"
        await anyio.Path(test_file).write_text("original content\n")

        # Register in document state
        uri = test_file.as_uri()
        client._document_state.register(uri, "original content\n", version=0)

        # Apply edit: text edit + rename + create
        new_file = temp_path / "renamed.py"
        created_file = temp_path / "new.py"

        request = lsp_type.ApplyWorkspaceEditRequest(
            id="test-6",
            params=lsp_type.ApplyWorkspaceEditParams(
                edit=lsp_type.WorkspaceEdit(
                    document_changes=[
                        # First, edit the document
                        lsp_type.TextDocumentEdit(
                            text_document=lsp_type.OptionalVersionedTextDocumentIdentifier(
                                uri=uri, version=0
                            ),
                            edits=[
                                lsp_type.TextEdit(
                                    range=lsp_type.Range(
                                        start=lsp_type.Position(line=0, character=0),
                                        end=lsp_type.Position(line=0, character=8),
                                    ),
                                    new_text="modified",
                                )
                            ],
                        ),
                        # Then rename it
                        lsp_type.RenameFile(old_uri=uri, new_uri=new_file.as_uri()),
                        # And create a new file
                        lsp_type.CreateFile(uri=created_file.as_uri()),
                    ]
                )
            ),
        )

        response = await client.respond_apply_edit(request)
        assert response.result.applied is True

        # Verify file operations
        assert not await anyio.Path(test_file).exists()
        assert await anyio.Path(new_file).exists()
        assert await anyio.Path(created_file).exists()
        assert await anyio.Path(new_file).read_text() == "modified content\n"

        # Verify document state updated
        with pytest.raises(KeyError):
            client._document_state.get_version(uri)
        assert client._document_state.get_version(new_file.as_uri()) == 1
