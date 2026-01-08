from __future__ import annotations

import tempfile
from pathlib import Path

import anyio
import pytest
from lsprotocol import types as lsp_type

from lsp_client.client.document_state import DocumentStateManager
from lsp_client.exception import EditApplicationError, VersionMismatchError
from lsp_client.utils.types import AnyPath
from lsp_client.utils.workspace_edit import WorkspaceEditApplicator, apply_text_edits


class MockClient:
    """Mock client for testing workspace edit application."""

    def __init__(self, temp_dir: Path | None = None) -> None:
        self.document_state = DocumentStateManager()
        self._files: dict[str, str] = {}
        self._temp_dir = temp_dir

    def get_document_state(self) -> DocumentStateManager:
        return self.document_state

    async def read_file(self, file_path: AnyPath) -> str:
        if self._temp_dir:
            # Read from actual filesystem if temp_dir is set
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
            # Write to actual filesystem if temp_dir is set
            path = uri.replace("file://", "")
            await anyio.Path(path).write_text(content)
        else:
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
    """Test applying multiple edits correctly regardless of input order."""
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
    # Deleting from character 5 to 16 removes ' beautiful ' (space + 'beautiful' + space)
    assert result == "Helloworld\n"


def test_apply_text_edits_snippet():
    """Test applying SnippetTextEdit edits."""
    content = "Hello world\n"
    edits = [
        lsp_type.SnippetTextEdit(
            range=lsp_type.Range(
                start=lsp_type.Position(line=0, character=6),
                end=lsp_type.Position(line=0, character=11),
            ),
            snippet=lsp_type.StringValue(value="snippet"),
        )
    ]
    result = apply_text_edits(content, edits)
    assert result == "Hello snippet\n"


@pytest.mark.asyncio
async def test_workspace_edit_applicator_simple():
    """Test applying a simple workspace edit."""
    client = MockClient()
    client._files["/test.py"] = "print('hello')\n"
    client.document_state.register("file:///test.py", "print('hello')\n", version=0)

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

    await applicator.apply_workspace_edit(edit)
    assert client._files["/test.py"] == "print('world')\n"
    assert client.document_state.get_version("file:///test.py") == 1


@pytest.mark.asyncio
async def test_workspace_edit_applicator_version_mismatch():
    """Test that version mismatch raises exception."""
    client = MockClient()
    client._files["/test.py"] = "print('hello')\n"
    client.document_state.register("file:///test.py", "print('hello')\n", version=5)

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

    with pytest.raises(VersionMismatchError) as exc_info:
        await applicator.apply_workspace_edit(edit)

    assert "Version mismatch" in str(exc_info.value)


@pytest.mark.asyncio
async def test_workspace_edit_applicator_untracked_document():
    """Test that editing untracked document raises exception."""
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

    with pytest.raises(EditApplicationError) as exc_info:
        await applicator.apply_workspace_edit(edit)

    assert "not open in client" in str(exc_info.value)


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

    await applicator.apply_workspace_edit(edit)
    assert client._files["/test.py"] == "print('world')\n"


@pytest.mark.asyncio
async def test_workspace_edit_empty():
    """Test applying an empty workspace edit."""
    client = MockClient()
    applicator = WorkspaceEditApplicator(client=client)

    # Test with no document_changes and no changes
    edit = lsp_type.WorkspaceEdit()
    await applicator.apply_workspace_edit(edit)

    # Test with empty document_changes
    edit = lsp_type.WorkspaceEdit(document_changes=[])
    await applicator.apply_workspace_edit(edit)

    # Test with empty changes dict
    edit = lsp_type.WorkspaceEdit(changes={})
    await applicator.apply_workspace_edit(edit)


@pytest.mark.asyncio
async def test_create_file():
    """Test CreateFile resource operation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        client = MockClient(temp_dir=temp_path)
        applicator = WorkspaceEditApplicator(client=client)

        new_file = temp_path / "new_file.txt"
        edit = lsp_type.WorkspaceEdit(
            document_changes=[lsp_type.CreateFile(uri=new_file.as_uri())]
        )

        await applicator.apply_workspace_edit(edit)
        assert await anyio.Path(new_file).exists()


@pytest.mark.asyncio
async def test_create_file_with_overwrite():
    """Test CreateFile with overwrite option."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        client = MockClient(temp_dir=temp_path)
        applicator = WorkspaceEditApplicator(client=client)

        existing_file = temp_path / "existing.txt"
        await anyio.Path(existing_file).write_text("original content")

        edit = lsp_type.WorkspaceEdit(
            document_changes=[
                lsp_type.CreateFile(
                    uri=existing_file.as_uri(),
                    options=lsp_type.CreateFileOptions(overwrite=True),
                )
            ]
        )

        await applicator.apply_workspace_edit(edit)


@pytest.mark.asyncio
async def test_create_file_ignore_if_exists():
    """Test CreateFile with ignoreIfExists option."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        client = MockClient(temp_dir=temp_path)
        applicator = WorkspaceEditApplicator(client=client)

        existing_file = temp_path / "existing.txt"
        await anyio.Path(existing_file).write_text("original content")

        edit = lsp_type.WorkspaceEdit(
            document_changes=[
                lsp_type.CreateFile(
                    uri=existing_file.as_uri(),
                    options=lsp_type.CreateFileOptions(ignore_if_exists=True),
                )
            ]
        )

        await applicator.apply_workspace_edit(edit)
        assert await anyio.Path(existing_file).read_text() == "original content"


@pytest.mark.asyncio
async def test_rename_file():
    """Test RenameFile resource operation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        client = MockClient(temp_dir=temp_path)
        applicator = WorkspaceEditApplicator(client=client)

        old_file = temp_path / "old.txt"
        await anyio.Path(old_file).write_text("content")

        new_file = temp_path / "new.txt"
        edit = lsp_type.WorkspaceEdit(
            document_changes=[
                lsp_type.RenameFile(
                    old_uri=old_file.as_uri(), new_uri=new_file.as_uri()
                )
            ]
        )

        await applicator.apply_workspace_edit(edit)
        assert not await anyio.Path(old_file).exists()
        assert await anyio.Path(new_file).exists()
        assert await anyio.Path(new_file).read_text() == "content"


@pytest.mark.asyncio
async def test_rename_file_with_document_state():
    """Test RenameFile updates document state."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        client = MockClient(temp_dir=temp_path)
        applicator = WorkspaceEditApplicator(client=client)

        old_file = temp_path / "old.txt"
        await anyio.Path(old_file).write_text("content")
        old_uri = old_file.as_uri()
        client.document_state.register(old_uri, "content", version=5)

        new_file = temp_path / "new.txt"
        new_uri = new_file.as_uri()
        edit = lsp_type.WorkspaceEdit(
            document_changes=[lsp_type.RenameFile(old_uri=old_uri, new_uri=new_uri)]
        )

        await applicator.apply_workspace_edit(edit)

        with pytest.raises(KeyError):
            client.document_state.get_version(old_uri)

        assert client.document_state.get_version(new_uri) == 5
        assert client.document_state.get_content(new_uri) == "content"


@pytest.mark.asyncio
async def test_delete_file():
    """Test DeleteFile resource operation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        client = MockClient(temp_dir=temp_path)
        applicator = WorkspaceEditApplicator(client=client)

        file_to_delete = temp_path / "delete_me.txt"
        await anyio.Path(file_to_delete).write_text("content")

        edit = lsp_type.WorkspaceEdit(
            document_changes=[lsp_type.DeleteFile(uri=file_to_delete.as_uri())]
        )

        await applicator.apply_workspace_edit(edit)
        assert not await anyio.Path(file_to_delete).exists()


@pytest.mark.asyncio
async def test_delete_file_with_document_state():
    """Test DeleteFile removes from document state."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        client = MockClient(temp_dir=temp_path)
        applicator = WorkspaceEditApplicator(client=client)

        file_to_delete = temp_path / "delete_me.txt"
        await anyio.Path(file_to_delete).write_text("content")
        uri = file_to_delete.as_uri()
        client.document_state.register(uri, "content", version=3)

        edit = lsp_type.WorkspaceEdit(document_changes=[lsp_type.DeleteFile(uri=uri)])

        await applicator.apply_workspace_edit(edit)

        with pytest.raises(KeyError):
            client.document_state.get_version(uri)


@pytest.mark.asyncio
async def test_delete_directory_recursive():
    """Test DeleteFile with recursive directory deletion."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        client = MockClient(temp_dir=temp_path)
        applicator = WorkspaceEditApplicator(client=client)

        dir_to_delete = temp_path / "dir"
        await anyio.Path(dir_to_delete).mkdir()
        await anyio.Path(dir_to_delete / "file1.txt").write_text("content1")
        await anyio.Path(dir_to_delete / "file2.txt").write_text("content2")

        edit = lsp_type.WorkspaceEdit(
            document_changes=[
                lsp_type.DeleteFile(
                    uri=dir_to_delete.as_uri(),
                    options=lsp_type.DeleteFileOptions(recursive=True),
                )
            ]
        )

        await applicator.apply_workspace_edit(edit)
        assert not await anyio.Path(dir_to_delete).exists()


@pytest.mark.asyncio
async def test_create_file_error_already_exists():
    """Test CreateFile raises error when file already exists without overwrite."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        client = MockClient(temp_dir=temp_path)
        applicator = WorkspaceEditApplicator(client=client)

        existing_file = temp_path / "existing.txt"
        await anyio.Path(existing_file).write_text("original content")

        edit = lsp_type.WorkspaceEdit(
            document_changes=[lsp_type.CreateFile(uri=existing_file.as_uri())]
        )

        with pytest.raises(EditApplicationError, match="already exists"):
            await applicator.apply_workspace_edit(edit)


@pytest.mark.asyncio
async def test_rename_file_error_source_not_exists():
    """Test RenameFile raises error when source file does not exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        client = MockClient(temp_dir=temp_path)
        applicator = WorkspaceEditApplicator(client=client)

        non_existent = temp_path / "non_existent.txt"
        new_file = temp_path / "new.txt"
        edit = lsp_type.WorkspaceEdit(
            document_changes=[
                lsp_type.RenameFile(
                    old_uri=non_existent.as_uri(), new_uri=new_file.as_uri()
                )
            ]
        )

        with pytest.raises(EditApplicationError, match="does not exist"):
            await applicator.apply_workspace_edit(edit)


@pytest.mark.asyncio
async def test_rename_file_error_target_exists():
    """Test RenameFile raises error when target file exists without overwrite."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        client = MockClient(temp_dir=temp_path)
        applicator = WorkspaceEditApplicator(client=client)

        old_file = temp_path / "old.txt"
        await anyio.Path(old_file).write_text("old content")
        new_file = temp_path / "new.txt"
        await anyio.Path(new_file).write_text("new content")

        edit = lsp_type.WorkspaceEdit(
            document_changes=[
                lsp_type.RenameFile(
                    old_uri=old_file.as_uri(), new_uri=new_file.as_uri()
                )
            ]
        )

        with pytest.raises(EditApplicationError, match="already exists"):
            await applicator.apply_workspace_edit(edit)


@pytest.mark.asyncio
async def test_delete_file_error_not_exists():
    """Test DeleteFile raises error when file does not exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        client = MockClient(temp_dir=temp_path)
        applicator = WorkspaceEditApplicator(client=client)

        non_existent = temp_path / "non_existent.txt"
        edit = lsp_type.WorkspaceEdit(
            document_changes=[lsp_type.DeleteFile(uri=non_existent.as_uri())]
        )

        with pytest.raises(EditApplicationError, match="does not exist"):
            await applicator.apply_workspace_edit(edit)
