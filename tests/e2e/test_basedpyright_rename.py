from __future__ import annotations

import anyio
import pytest

from lsp_client.clients.basedpyright import BasedpyrightClient
from lsp_client.utils.types import Position
from tests.framework.lsp import lsp_interaction_context


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_basedpyright_rename():
    async with lsp_interaction_context(BasedpyrightClient) as interaction:  # ty: ignore[invalid-argument-type]
        content = "def my_func():\n    pass\n\nmy_func()\n"
        file_path = "test_rename.py"
        full_path = await interaction.create_file(file_path, content)

        # We don't need to manually open the file because request_rename handles it now,
        # but in a real scenario it might already be open.
        success = await interaction.client.request_rename(  # ty: ignore[unresolved-attribute]
            full_path, Position(line=0, character=4), "new_func"
        )

        assert success is True

        updated_content = full_path.read_text()
        assert "def new_func():" in updated_content
        assert "new_func()" in updated_content
        assert "my_func" not in updated_content


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_basedpyright_rename_multiple_files():
    async with lsp_interaction_context(BasedpyrightClient) as interaction:  # ty: ignore[invalid-argument-type]
        # File 1: defines a function
        content1 = "def my_global_func():\n    pass\n"
        path1 = await interaction.create_file("lib.py", content1)

        # File 2: uses the function
        content2 = "from lib import my_global_func\nmy_global_func()\n"
        path2 = await interaction.create_file("main.py", content2)

        await anyio.sleep(2)  # Wait for indexing

        # Perform rename in lib.py

        success = await interaction.client.request_rename(  # ty: ignore[unresolved-attribute]
            path1, Position(line=0, character=4), "new_global_func"
        )

        assert success is True

        # Verify lib.py
        assert "def new_global_func():" in path1.read_text()

        # Verify main.py (cross-file rename)
        main_content = path2.read_text()
        assert "from lib import new_global_func" in main_content
        assert "new_global_func()" in main_content
        assert "my_global_func" not in main_content
