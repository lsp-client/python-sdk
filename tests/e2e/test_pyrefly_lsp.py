from __future__ import annotations

from pathlib import Path

import pytest

from lsp_client.clients.pyrefly import PyreflyClient
from tests.framework.lsp import lsp_interaction_context

# Fixtures are in the parent fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "pyrefly_lsp"


@pytest.mark.e2e
@pytest.mark.requires_fixtures
@pytest.mark.asyncio
async def test_pyrefly_go_to_def_relative():
    # References: references/pyrefly/pyrefly/lib/test/lsp/lsp_interaction/definition.rs:165
    # File: basic/foo_relative.py
    workspace_root = FIXTURES_DIR / "basic"
    async with lsp_interaction_context(
        PyreflyClient,  # ty: ignore[invalid-argument-type]
        workspace_root=workspace_root,
    ) as interaction:
        # Line 6: from .bar import Bar; Bar().foo
        # Pyrefly returns the attribute access position for property access,
        # not the definition position of the class attribute.
        assertion = await interaction.request_definition("foo_relative.py", 6, 17)
        assertion.expect_definition("foo_relative.py", 6, 14, 6, 17)

        # Line 8: bar.Bar().foo
        assertion = await interaction.request_definition("foo_relative.py", 8, 9)
        assertion.expect_definition("foo_relative.py", 7, 17, 7, 20)


@pytest.mark.e2e
@pytest.mark.requires_fixtures
@pytest.mark.asyncio
async def test_pyrefly_hover_primitive():
    # References: references/pyrefly/pyrefly/lib/test/lsp/lsp_interaction/test_files/primitive_type_test.py
    workspace_root = FIXTURES_DIR
    async with lsp_interaction_context(
        PyreflyClient,  # ty: ignore[invalid-argument-type]
        workspace_root=workspace_root,
    ) as interaction:
        await interaction.create_file("primitive_test.py", "x: int = 1\ny: str = 'hi'")

        assertion = await interaction.request_hover("primitive_test.py", 0, 0)
        assertion.expect_content("int")

        assertion = await interaction.request_hover("primitive_test.py", 1, 0)
        assertion.expect_content("str")
