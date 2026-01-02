from __future__ import annotations

from pathlib import Path

import pytest

from lsp_client.clients.pyrefly import PyreflyClient
from tests.framework.lsp import lsp_interaction_context

# Fixtures are in the parent fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "pyrefly"


@pytest.mark.e2e
@pytest.mark.requires_fixtures
@pytest.mark.asyncio
async def test_pyrefly_conformance_protocols():
    """Test protocol conformance with pyrefly.

    This test is currently skipped because it depends on pyrefly's own
    conformance test project (including ``protocols_definition.py`` and its
    configuration), which is not included in this repository's fixtures.

    To enable this test in the future, add the pyrefly conformance project
    under ``FIXTURES_DIR`` so that ``protocols_definition.py`` and its
    expected configuration are available, and then remove the unconditional
    ``pytest.skip`` call below.
    """
    pytest.skip(
        "Skipped: requires pyrefly's conformance project (protocols_definition.py "
        "and its configuration) to be present under FIXTURES_DIR."
    )


@pytest.mark.e2e
@pytest.mark.requires_fixtures
@pytest.mark.asyncio
async def test_pyrefly_conformance_generics():
    """Test generics conformance with pyrefly."""
    async with lsp_interaction_context(
        PyreflyClient,  # ty: ignore[invalid-argument-type]
        workspace_root=FIXTURES_DIR,
    ) as interaction:
        # Test definition of 'first' in test_first
        # Line 23: assert_type(first(seq_int), int)
        assertion = await interaction.request_definition("generics_basic.py", 22, 16)
        assertion.expect_definition("generics_basic.py", 17, 4, 17, 9)

        # Test hover on TypeVar T
        assertion = await interaction.request_hover("generics_basic.py", 11, 0)
        assertion.expect_content("T")
