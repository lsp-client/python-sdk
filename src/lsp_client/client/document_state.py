from __future__ import annotations

from attrs import Factory, define, frozen


@frozen
class DocumentState:
    """
    Represents the state of a single open document.

    Attributes:
        content: Current text content of the document
        version: Current version number (incremented on each change)
    """

    content: str
    version: int


@define
class DocumentStateManager:
    """
    Manages mutable state of open text documents.

    Tracks URI -> DocumentState mapping for version increments and content updates.
    Version numbers start at 0 for newly opened documents and increment with each
    change notification.

    All operations are synchronous and safe in single-threaded async event loops
    since dict operations are atomic and there are no await points in any method.

    Attributes:
        _states: Maps document URI to its current state
    """

    _states: dict[str, DocumentState] = Factory(dict)

    def register(self, uri: str, content: str, version: int = 0) -> None:
        """
        Register a newly opened document.

        Args:
            uri: Document URI
            content: Initial document content
            version: Initial version (defaults to 0)

        Raises:
            KeyError: If the document URI is already registered
        """
        if uri in self._states:
            raise KeyError(f"Document {uri} is already registered in state manager")
        self._states[uri] = DocumentState(content=content, version=version)

    def unregister(self, uri: str) -> None:
        """
        Unregister a closed document.

        Args:
            uri: Document URI

        Raises:
            KeyError: If document URI is not registered
        """
        if uri in self._states:
            del self._states[uri]
            return
        raise KeyError(f"Document {uri} not found in state manager")

    def get_version(self, uri: str) -> int:
        """
        Get current version of a document.

        Args:
            uri: Document URI

        Returns:
            Current version number

        Raises:
            KeyError: If document URI is not registered
        """
        if state := self._states.get(uri):
            return state.version
        raise KeyError(f"Document {uri} not found in state manager")

    def get_content(self, uri: str) -> str:
        """
        Get current content of a document.

        Args:
            uri: Document URI

        Returns:
            Current document content

        Raises:
            KeyError: If document URI is not registered
        """
        if state := self._states.get(uri):
            return state.content
        raise KeyError(f"Document {uri} not found in state manager")

    def increment_version(self, uri: str) -> int:
        """
        Increment version and return the new version.

        Args:
            uri: Document URI

        Returns:
            New version number after increment

        Raises:
            KeyError: If document URI is not registered
        """
        if state := self._states.get(uri):
            new_version = state.version + 1
            self._states[uri] = DocumentState(
                content=state.content, version=new_version
            )
            return new_version
        raise KeyError(f"Document {uri} not found in state manager")

    def update_content(self, uri: str, content: str) -> int:
        """
        Update content and increment version atomically.

        Args:
            uri: Document URI
            content: New document content

        Returns:
            New version number after update

        Raises:
            KeyError: If document URI is not registered
        """
        if state := self._states.get(uri):
            new_version = state.version + 1
            self._states[uri] = DocumentState(content=content, version=new_version)
            return new_version
        raise KeyError(f"Document {uri} not found in state manager")
