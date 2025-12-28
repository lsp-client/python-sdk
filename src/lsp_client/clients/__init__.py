from __future__ import annotations

from typing import Final

from .deno import DenoClient
from .gopls import GoplsClient
from .language_client import Language, LanguageClient
from .pyrefly import PyreflyClient
from .pyright import PyrightClient
from .rust_analyzer import RustAnalyzerClient
from .ty import TyClient
from .typescript import TypescriptClient

GoClient = GoplsClient
PythonClient = PyrightClient
RustClient = RustAnalyzerClient
TypeScriptClient = TypescriptClient

clients: Final = (
    GoplsClient,
    PyreflyClient,
    PyrightClient,
    RustAnalyzerClient,
    DenoClient,
    TypescriptClient,
    TyClient,
)

__all__ = [
    "DenoClient",
    "GoClient",
    "GoplsClient",
    "Language",
    "LanguageClient",
    "PyreflyClient",
    "PythonClient",
    "RustClient",
    "TyClient",
    "TypeScriptClient",
]
