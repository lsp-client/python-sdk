from __future__ import annotations

from pathlib import Path

import pytest
from lsprotocol import types as lsp_type

from lsp_client.client.document_state import DocumentStateManager
from lsp_client.utils.workspace_edit import WorkspaceEditApplicator, apply_text_edits


class MockClient:
    """Mock client for testing workspace edit application."""

    def __init__(self) -> None:
        self._document_state = DocumentStateManager()
        self._files: dict[str, str] = {}

    async def read_file(self, file_path: str | Path) -> str:
        path_str = str(file_path)
        if path_str not in self._files:
            raise FileNotFoundError(f"File not found: {file_path}")
        return self._files[path_str]

    async def write_file(self, uri: str, content: str) -> None:
        # Extract path from URI for simplicity
        path = uri.replace("file://", "")
        self._files[path] = content

    def from_uri(self, uri: str, *, relative: bool = True) -> Path:
        # Simple URI to path conversion
        return Path(uri.replace("file://", ""))


def test_apply_text_edits_single_line():
    """Test applying a single text edit to one line."""
    content = "Hello world\n"
    edits = [
        lsp_type.TextEdit(
            range=lsp_type.Range(
                start=lsp_type.Position(line=0, character=6),
                end=lsp_type.Position(line=0, character=11),
            ),
            new_text="Python",
        )
    ]
    result = apply_text_edits(content, edits)
    assert result == "Hello Python\n"


def test_apply_text_edits_multiple_edits():
    """Test applying multiple edits in reverse order."""
    content = "line 1\nline 2\nline 3\n"
    edits = [
        lsp_type.TextEdit(
            range=lsp_type.Range(
                start=lsp_type.Position(line=0, character=5),
                end=lsp_type.Position(line=0, character=6),
            ),
            new_text="one",
        ),
        lsp_type.TextEdit(
            range=lsp_type.Range(
                start=lsp_type.Position(line=1, character=5),
                end=lsp_type.Position(line=1, character=6),
            ),
            new_text="two",
        ),
    ]
    result = apply_text_edits(content, edits)
    assert result == "line one\nline two\nline 3\n"


def test_apply_text_edits_multiline():
    """Test applying an edit that spans multiple lines."""
    content = "line 1\nline 2\nline 3\n"
    edits = [
        lsp_type.TextEdit(
            range=lsp_type.Range(
                start=lsp_type.Position(line=0, character=0),
                end=lsp_type.Position(line=2, character=0),
            ),
            new_text="replaced\n",
        )
    ]
    result = apply_text_edits(content, edits)
    assert result == "replaced\nline 3\n"


def test_apply_text_edits_insertion():
    """Test inserting text without replacing anything."""
    content = "Hello world\n"
    edits = [
        lsp_type.TextEdit(
            range=lsp_type.Range(
                start=lsp_type.Position(line=0, character=5),
                end=lsp_type.Position(line=0, character=5),
            ),
            new_text=" beautiful",
        )
    ]
    result = apply_text_edits(content, edits)
    assert result == "Hello beautiful world\n"


def test_apply_text_edits_deletion():
    """Test deleting text."""
    content = "Hello beautiful world\n"
    edits = [
        lsp_type.TextEdit(
            range=lsp_type.Range(
                start=lsp_type.Position(line=0, character=5),
                end=lsp_type.Position(line=0, character=16),
            ),
            new_text="",
        )
    ]
    result = apply_text_edits(content, edits)
    # Deleting from character 5 to 16 removes " beautiful " (including surrounding spaces)
    assert result == "Helloworld\n"


@pytest.mark.asyncio
async def test_workspace_edit_applicator_simple():
    """Test applying a simple workspace edit."""
    client = MockClient()
    client._files["/test.py"] = "print('hello')\n"
    client._document_state.register("file:///test.py", "print('hello')\n", version=0)

    applicator = WorkspaceEditApplicator(client=client)
    edit = lsp_type.WorkspaceEdit(
        document_changes=[
            lsp_type.TextDocumentEdit(
                text_document=lsp_type.OptionalVersionedTextDocumentIdentifier(
                    uri="file:///test.py", version=0
                ),
                edits=[
                    lsp_type.TextEdit(
                        range=lsp_type.Range(
                            start=lsp_type.Position(line=0, character=7),
                            end=lsp_type.Position(line=0, character=12),
                        ),
                        new_text="world",
                    )
                ],
            )
        ]
    )

    success, error = await applicator.apply_workspace_edit(edit)
    assert success
    assert error is None
    assert client._files["/test.py"] == "print('world')\n"
    assert client._document_state.get_version("file:///test.py") == 1


@pytest.mark.asyncio
async def test_workspace_edit_applicator_version_mismatch():
    """Test that version mismatch is detected."""
    client = MockClient()
    client._files["/test.py"] = "print('hello')\n"
    client._document_state.register("file:///test.py", "print('hello')\n", version=5)

    applicator = WorkspaceEditApplicator(client=client)
    edit = lsp_type.WorkspaceEdit(
        document_changes=[
            lsp_type.TextDocumentEdit(
                text_document=lsp_type.OptionalVersionedTextDocumentIdentifier(
                    uri="file:///test.py",
                    version=0,  # Wrong version
                ),
                edits=[
                    lsp_type.TextEdit(
                        range=lsp_type.Range(
                            start=lsp_type.Position(line=0, character=7),
                            end=lsp_type.Position(line=0, character=12),
                        ),
                        new_text="world",
                    )
                ],
            )
        ]
    )

    success, error = await applicator.apply_workspace_edit(edit)
    assert not success
    assert error is not None
    assert "Version mismatch" in error


@pytest.mark.asyncio
async def test_workspace_edit_applicator_untracked_document():
    """Test that editing untracked document fails."""
    client = MockClient()
    client._files["/test.py"] = "print('hello')\n"

    applicator = WorkspaceEditApplicator(client=client)
    edit = lsp_type.WorkspaceEdit(
        document_changes=[
            lsp_type.TextDocumentEdit(
                text_document=lsp_type.OptionalVersionedTextDocumentIdentifier(
                    uri="file:///test.py", version=0
                ),
                edits=[
                    lsp_type.TextEdit(
                        range=lsp_type.Range(
                            start=lsp_type.Position(line=0, character=7),
                            end=lsp_type.Position(line=0, character=12),
                        ),
                        new_text="world",
                    )
                ],
            )
        ]
    )

    success, error = await applicator.apply_workspace_edit(edit)
    assert not success
    assert error is not None
    assert "not open in client" in error


@pytest.mark.asyncio
async def test_workspace_edit_applicator_changes_format():
    """Test applying workspace edit using deprecated changes format."""
    client = MockClient()
    client._files["/test.py"] = "print('hello')\n"

    applicator = WorkspaceEditApplicator(client=client)
    edit = lsp_type.WorkspaceEdit(
        changes={
            "file:///test.py": [
                lsp_type.TextEdit(
                    range=lsp_type.Range(
                        start=lsp_type.Position(line=0, character=7),
                        end=lsp_type.Position(line=0, character=12),
                    ),
                    new_text="world",
                )
            ]
        }
    )

    success, error = await applicator.apply_workspace_edit(edit)
    assert success
    assert error is None
    assert client._files["/test.py"] == "print('world')\n"
