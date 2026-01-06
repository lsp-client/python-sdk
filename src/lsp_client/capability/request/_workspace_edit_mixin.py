from __future__ import annotations

from typing import Protocol, runtime_checkable

from lsp_client.utils.types import lsp_type
from lsp_client.utils.workspace_edit import (
    DocumentEditProtocol,
    WorkspaceEditApplicator,
)


@runtime_checkable
class WithApplyWorkspaceEdit(DocumentEditProtocol, Protocol):
    """
    Mixin that provides workspace edit application functionality.

    This mixin provides a helper method for applying workspace edits
    returned from LSP requests. It's used by capabilities that return
    WorkspaceEdit objects (e.g., rename, willCreateFiles, etc.).
    """

    async def apply_workspace_edit(self, edit: lsp_type.WorkspaceEdit) -> None:
        """
        Apply workspace edit to documents.

        This is a helper method that provides a convenient way to apply
        workspace edits returned from various LSP requests.

        Args:
            edit: Workspace edit to apply

        Raises:
            EditApplicationError: If edit cannot be applied due to business logic
            VersionMismatchError: If document version doesn't match expected version
            OSError: If file I/O operations fail
            ValueError: If edit contains invalid data

        Example:
            >>> edit = await client.request_rename_edits(file, pos, "new_name")
            >>> if edit:
            >>>     try:
            >>>         await client.apply_workspace_edit(edit)
            >>>         print("Changes applied")
            >>>     except EditApplicationError as e:
            >>>         print(f"Failed: {e.message}")
        """
        applicator = WorkspaceEditApplicator(client=self)
        await applicator.apply_workspace_edit(edit)
