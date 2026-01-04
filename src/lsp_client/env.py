from __future__ import annotations

from lsp_client.settings import settings


def disable_auto_installation() -> bool:
    return settings.disable_auto_installation
