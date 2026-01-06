from __future__ import annotations

import pytest

from lsp_client.client.document_state import DocumentState, DocumentStateManager


def test_document_state_immutable():
    state = DocumentState(content="hello", version=0)
    assert state.content == "hello"
    assert state.version == 0


def test_register_document():
    manager = DocumentStateManager()
    manager.register("file:///test.py", "print('hello')", version=0)

    assert manager.get_version("file:///test.py") == 0
    assert manager.get_content("file:///test.py") == "print('hello')"


def test_unregister_document():
    manager = DocumentStateManager()
    manager.register("file:///test.py", "print('hello')")
    manager.unregister("file:///test.py")

    with pytest.raises(KeyError):
        manager.get_version("file:///test.py")


def test_increment_version():
    manager = DocumentStateManager()
    manager.register("file:///test.py", "print('hello')", version=0)

    new_version = manager.increment_version("file:///test.py")
    assert new_version == 1
    assert manager.get_version("file:///test.py") == 1
    assert manager.get_content("file:///test.py") == "print('hello')"


def test_update_content():
    manager = DocumentStateManager()
    manager.register("file:///test.py", "print('hello')", version=0)

    new_version = manager.update_content("file:///test.py", "print('world')")
    assert new_version == 1
    assert manager.get_version("file:///test.py") == 1
    assert manager.get_content("file:///test.py") == "print('world')"


def test_multiple_documents():
    manager = DocumentStateManager()
    manager.register("file:///test1.py", "content1", version=0)
    manager.register("file:///test2.py", "content2", version=5)

    assert manager.get_version("file:///test1.py") == 0
    assert manager.get_version("file:///test2.py") == 5

    manager.increment_version("file:///test1.py")
    assert manager.get_version("file:///test1.py") == 1
    assert manager.get_version("file:///test2.py") == 5


def test_get_version_nonexistent():
    manager = DocumentStateManager()
    with pytest.raises(KeyError, match=r"Document .* not found"):
        manager.get_version("file:///nonexistent.py")


def test_get_content_nonexistent():
    manager = DocumentStateManager()
    with pytest.raises(KeyError, match=r"Document .* not found"):
        manager.get_content("file:///nonexistent.py")


def test_increment_version_nonexistent():
    manager = DocumentStateManager()
    with pytest.raises(KeyError, match=r"Document .* not found"):
        manager.increment_version("file:///nonexistent.py")


def test_update_content_nonexistent():
    manager = DocumentStateManager()
    with pytest.raises(KeyError, match=r"Document .* not found"):
        manager.update_content("file:///nonexistent.py", "new content")


def test_register_document_twice():
    """Test that registering a document twice raises KeyError."""
    manager = DocumentStateManager()
    manager.register("file:///test.py", "print('hello')", version=0)

    with pytest.raises(KeyError, match=r"Document .* is already registered"):
        manager.register("file:///test.py", "print('world')", version=0)


def test_unregister_nonexistent_document():
    """Test that unregistering a non-existent document raises KeyError."""
    manager = DocumentStateManager()

    with pytest.raises(KeyError, match=r"Document .* not found"):
        manager.unregister("file:///nonexistent.py")
