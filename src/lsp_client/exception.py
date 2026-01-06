from __future__ import annotations

from attrs import frozen


class LSPError(Exception):
    """Base exception for all lsp-client errors."""


@frozen
class EditApplicationError(LSPError):
    """Error occurred while applying workspace edits."""

    message: str
    uri: str | None = None

    def __str__(self) -> str:
        return self.message


@frozen
class VersionMismatchError(EditApplicationError):
    """Document version mismatch during edit application."""

    expected_version: int | None = None
    actual_version: int | None = None
