from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from functools import cached_property
from pathlib import Path

import anyio
import asyncer
from attrs import Factory, define, frozen

from lsp_client.utils.workspace import from_local_uri


@frozen
class LSPFileBufferItem:
    """
    Represents an open file buffer in the LSP client.

    Stores file content and metadata for files being synchronized with
    the language server. Uses reference counting to track multiple opens
    of the same file.

    Attributes:
        file_uri: The URI of the file
        file_content: Raw byte content of the file

    Properties:
        file_path: Local filesystem Path derived from the URI
        content: Decoded UTF-8 string content

    Example:
        item = LSPFileBufferItem(file_uri="file:///test.py", file_content=b"print('hello')")
        print(item.content)  # "print('hello')"
        print(item.file_path)  # PosixPath('/test.py')
    """

    file_uri: str
    file_content: bytes

    @cached_property
    def file_path(self) -> Path:
        return from_local_uri(self.file_uri)

    @cached_property
    def content(self) -> str:
        return self.file_content.decode("utf-8")


@define
class LSPFileBuffer:
    """
    Manages file buffers for LSP document synchronization.

    Provides efficient opening and closing of multiple files with reference
    counting support. Files are cached in memory and synchronized with the
    language server through notifications.

    The buffer maintains a lookup dictionary and reference counter for each
    open file, ensuring proper cleanup when files are closed multiple times.

    Attributes:
        _lookup: Maps file URIs to their buffer items
        _ref_count: Tracks how many times each file is open

    Example:
        buffer = LSPFileBuffer()
        items = await buffer.open(["file:///test.py", "file:///lib.py"])
        # Files are now tracked
        closed = buffer.close(["file:///test.py"])
        # Files with ref_count 0 are removed from lookup
    """

    _lookup: dict[str, LSPFileBufferItem] = Factory(dict)
    _ref_count: Counter[str] = Factory(Counter)

    async def open(self, file_uris: Iterable[str]) -> Sequence[LSPFileBufferItem]:
        """Open files and save to buffer. Only return newly opened files."""

        file_uris = list(file_uris)
        new_uris = [uri for uri in file_uris if uri not in self._lookup]

        items: list[LSPFileBufferItem] = []

        async def append_item(uri: str):
            text = await anyio.Path(from_local_uri(uri)).read_bytes()
            items.append(LSPFileBufferItem(file_uri=uri, file_content=text))

        async with asyncer.create_task_group() as tg:
            for uri in new_uris:
                tg.soonify(append_item)(uri)

        self._lookup.update({item.file_uri: item for item in items})
        self._ref_count.update(file_uris)

        return items

    def close(self, file_uris: Iterable[str]) -> Sequence[LSPFileBufferItem]:
        """
        Close the files. Return paths of files that are really closed (ref count reaches 0).
        """

        self._ref_count.subtract(file_uris)

        closed_items: list[LSPFileBufferItem] = []
        for uri, ref_count in self._ref_count.items():
            if ref_count > 0:
                continue
            if item := self._lookup.pop(uri, None):
                closed_items.append(item)

        return closed_items
