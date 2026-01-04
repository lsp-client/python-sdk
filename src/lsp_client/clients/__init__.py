from __future__ import annotations

from typing import Final

from .basedpyright import BasedpyrightClient
from .deno import DenoClient
from .gopls import GoplsClient
from .pyrefly import PyreflyClient
from .pyright import PyrightClient
from .rust_analyzer import RustAnalyzerClient
from .ty import TyClient
from .typescript import TypescriptClient

clients: Final = {
    "basedpyright": BasedpyrightClient,
    "gopls": GoplsClient,
    "pyrefly": PyreflyClient,
    "pyright": PyrightClient,
    "rust_analyzer": RustAnalyzerClient,
    "deno": DenoClient,
    "typescript": TypescriptClient,
    "ty": TyClient,
}

__all__ = [
    "BasedpyrightClient",
    "DenoClient",
    "GoplsClient",
    "PyreflyClient",
    "PyrightClient",
    "RustAnalyzerClient",
    "TyClient",
    "TypescriptClient",
]
