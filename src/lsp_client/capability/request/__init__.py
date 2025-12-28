from __future__ import annotations

from typing import Final

from .call_hierarchy import WithRequestCallHierarchy
from .code_action import WithRequestCodeAction
from .completion import WithRequestCompletion
from .declaration import WithRequestDeclaration
from .definition import WithRequestDefinition
from .document_symbol import WithRequestDocumentSymbol
from .hover import WithRequestHover
from .implementation import WithRequestImplementation
from .inlay_hint import WithRequestInlayHint
from .inline_value import WithRequestInlineValue
from .pull_diagnostic import WithRequestPullDiagnostic
from .reference import WithRequestReferences
from .signature_help import WithRequestSignatureHelp
from .type_definition import WithRequestTypeDefinition
from .type_hierarchy import WithRequestTypeHierarchy
from .workspace_symbol import WithRequestWorkspaceSymbol

capabilities: Final = (
    WithRequestCallHierarchy,
    WithRequestCodeAction,
    WithRequestCompletion,
    WithRequestDeclaration,
    WithRequestDefinition,
    WithRequestDocumentSymbol,
    WithRequestHover,
    WithRequestImplementation,
    WithRequestInlayHint,
    WithRequestInlineValue,
    WithRequestPullDiagnostic,
    WithRequestReferences,
    WithRequestSignatureHelp,
    WithRequestTypeDefinition,
    WithRequestTypeHierarchy,
    WithRequestWorkspaceSymbol,
)

__all__ = [
    "WithRequestCallHierarchy",
    "WithRequestCodeAction",
    "WithRequestCompletion",
    "WithRequestDeclaration",
    "WithRequestDefinition",
    "WithRequestDocumentSymbol",
    "WithRequestHover",
    "WithRequestImplementation",
    "WithRequestInlayHint",
    "WithRequestInlineValue",
    "WithRequestPullDiagnostic",
    "WithRequestReferences",
    "WithRequestSignatureHelp",
    "WithRequestTypeDefinition",
    "WithRequestTypeHierarchy",
    "WithRequestWorkspaceSymbol",
    "capabilities",
]
