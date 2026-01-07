from __future__ import annotations

import shutil

import anyio
import anyio.to_thread

from lsp_client.capability.notification.did_create_files import WithNotifyDidCreateFiles
from lsp_client.capability.notification.did_delete_files import WithNotifyDidDeleteFiles
from lsp_client.capability.notification.did_rename_files import WithNotifyDidRenameFiles
from lsp_client.capability.request.will_create_files import WithRequestWillCreateFiles
from lsp_client.capability.request.will_delete_files import WithRequestWillDeleteFiles
from lsp_client.capability.request.will_rename_files import WithRequestWillRenameFiles
from lsp_client.client.abc import Client
from lsp_client.utils.uri import from_local_uri


async def create_files_with_server(client: Client, uris: list[str]) -> None:
    """
    Create files with full LSP integration.

    This operation is not atomic. If interrupted between steps, the workspace
    may be left in an inconsistent state. Consider implementing error handling
    and rollback mechanisms for critical operations.

    1. Call willCreateFiles to get edits
    2. Apply workspace edits
    3. Create the files (if they don't exist)
    4. Call didCreateFiles notification

    Args:
        client: LSP client instance
        uris: List of file URIs to create

    Raises:
        EditApplicationError: If workspace edit cannot be applied
        OSError: If file system operations fail (e.g., permissions, disk full)
        ValueError: If URIs are invalid
    """
    if isinstance(client, WithRequestWillCreateFiles):
        edit = await client.request_will_create_files(uris)
        if edit:
            await client.apply_workspace_edit(edit)

    for uri in uris:
        path = from_local_uri(uri)
        anyio_path = anyio.Path(path)
        if not await anyio_path.exists():
            await anyio_path.parent.mkdir(parents=True, exist_ok=True)
            _ = await anyio_path.write_text("")

    if isinstance(client, WithNotifyDidCreateFiles):
        await client.notify_did_create_files(uris)


async def rename_files_with_server(
    client: Client, file_renames: list[tuple[str, str]]
) -> None:
    """
    Rename files with full LSP integration.

    This operation is not atomic. If interrupted between steps, the workspace
    may be left in an inconsistent state. Consider implementing error handling
    and rollback mechanisms for critical operations.

    1. Call willRenameFiles to get edits
    2. Apply workspace edits
    3. Rename the files
    4. Call didRenameFiles notification

    Args:
        client: LSP client instance
        file_renames: List of (old_uri, new_uri) tuples

    Raises:
        EditApplicationError: If workspace edit cannot be applied
        OSError: If file system operations fail (e.g., permissions, disk full)
        ValueError: If URIs are invalid
    """
    if isinstance(client, WithRequestWillRenameFiles):
        edit = await client.request_will_rename_files(file_renames)
        if edit:
            await client.apply_workspace_edit(edit)

    for old_uri, new_uri in file_renames:
        old_path = anyio.Path(from_local_uri(old_uri))
        new_path = anyio.Path(from_local_uri(new_uri))
        if await old_path.exists():
            await new_path.parent.mkdir(parents=True, exist_ok=True)
            _ = await old_path.rename(new_path)

    if isinstance(client, WithNotifyDidRenameFiles):
        await client.notify_did_rename_files(file_renames)


async def delete_files_with_server(client: Client, uris: list[str]) -> None:
    """
    Delete files with full LSP integration.

    This operation is not atomic. If interrupted between steps, the workspace
    may be left in an inconsistent state. Consider implementing error handling
    and rollback mechanisms for critical operations.

    1. Call willDeleteFiles to get edits
    2. Apply workspace edits
    3. Delete the files
    4. Call didDeleteFiles notification

    Args:
        client: LSP client instance
        uris: List of file URIs to delete

    Raises:
        EditApplicationError: If workspace edit cannot be applied
        OSError: If file system operations fail (e.g., permissions, disk full)
        ValueError: If URIs are invalid
    """
    if isinstance(client, WithRequestWillDeleteFiles):
        edit = await client.request_will_delete_files(uris)
        if edit:
            await client.apply_workspace_edit(edit)

    for uri in uris:
        path = anyio.Path(from_local_uri(uri))
        if await path.exists():
            if await path.is_dir():
                await anyio.to_thread.run_sync(shutil.rmtree, str(path))
            else:
                await path.unlink()

    if isinstance(client, WithNotifyDidDeleteFiles):
        await client.notify_did_delete_files(uris)
