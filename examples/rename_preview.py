"""
Example demonstrating how to preview rename changes before applying them.

This example shows how to use the request_rename_edits() method to get
WorkspaceEdit for preview, then optionally apply it.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from lsprotocol.types import Position, SnippetTextEdit, TextDocumentEdit

from lsp_client.clients import PyrightClient


async def preview_rename_example() -> None:
    """Show how to preview rename changes before applying."""
    workspace = Path.cwd()

    async with PyrightClient(workspace=workspace) as client:
        file_path = workspace / "example.py"
        position = Position(line=10, character=5)
        new_name = "new_variable_name"

        # Get workspace edits without applying them
        edits = await client.request_rename_edits(
            file_path=file_path,
            position=position,
            new_name=new_name,
        )

        if edits is None:
            print("Rename not possible at this position")
            return

        # Preview changes
        print(f"Renaming to '{new_name}' will affect:")

        if edits.document_changes:
            # Modern format with versioning
            for change in edits.document_changes:
                match change:
                    case TextDocumentEdit(text_document=doc, edits=text_edits):
                        uri = doc.uri
                        print(f"  {uri}: {len(text_edits)} changes")
                        for edit in text_edits:
                            # Extract range and new text
                            start = edit.range.start
                            end = edit.range.end

                            match edit:
                                case SnippetTextEdit(snippet=snippet):
                                    new_text = snippet.value
                                case _:
                                    # TextEdit or AnnotatedTextEdit
                                    new_text = edit.new_text

                            print(
                                f"    Line {start.line}:{start.character}-"
                                f"{end.line}:{end.character} -> '{new_text}'"
                            )
        elif edits.changes:
            # Legacy format
            for uri, text_edits in edits.changes.items():
                print(f"  {uri}: {len(text_edits)} changes")

        # Ask user for confirmation
        confirm = input("\nApply these changes? (y/n): ")

        if confirm.lower() == "y":
            # Apply the edits (Pythonic: raises exception on failure)
            try:
                await client.apply_workspace_edit(edits)
                print("✓ Rename completed successfully")
            except Exception as e:  # noqa: BLE001
                print(f"✗ Rename failed: {e}")
        else:
            print("Rename cancelled")


async def direct_rename_example() -> None:
    """Show how to apply rename directly without preview."""
    workspace = Path.cwd()

    async with PyrightClient(workspace=workspace) as client:
        file_path = workspace / "example.py"
        position = Position(line=10, character=5)
        new_name = "new_variable_name"

        # Apply rename directly (returns False if not possible, raises on error)
        try:
            success = await client.request_rename(
                file_path=file_path,
                position=position,
                new_name=new_name,
            )

            if success:
                print("✓ Rename completed successfully")
            else:
                print("✗ Rename not possible at this position")
        except Exception as e:  # noqa: BLE001
            print(f"✗ Rename failed: {e}")


if __name__ == "__main__":
    # Preview before applying
    asyncio.run(preview_rename_example())

    # Or apply directly
    # asyncio.run(direct_rename_example())
