from __future__ import annotations

from typing import Final

from ..diagnostic.document import WithDocumentDiagnostic
from ..diagnostic.workspace import WithWorkspaceDiagnostic
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
from .reference import WithRequestReferences
from .rename import WithRequestRename
from .signature_help import WithRequestSignatureHelp
from .type_definition import WithRequestTypeDefinition
from .type_hierarchy import WithRequestTypeHierarchy
from .will_create_files import WithRequestWillCreateFiles
from .will_delete_files import WithRequestWillDeleteFiles
from .will_rename_files import WithRequestWillRenameFiles
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
    WithDocumentDiagnostic,
    WithRequestReferences,
    WithRequestRename,
    WithRequestSignatureHelp,
    WithRequestTypeDefinition,
    WithRequestTypeHierarchy,
    WithRequestWillCreateFiles,
    WithRequestWillRenameFiles,
    WithRequestWillDeleteFiles,
    WithWorkspaceDiagnostic,
    WithRequestWorkspaceSymbol,
)

__all__ = [
    "WithDocumentDiagnostic",
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
    "WithRequestReferences",
    "WithRequestRename",
    "WithRequestSignatureHelp",
    "WithRequestTypeDefinition",
    "WithRequestTypeHierarchy",
    "WithRequestWillCreateFiles",
    "WithRequestWillDeleteFiles",
    "WithRequestWillRenameFiles",
    "WithRequestWorkspaceSymbol",
    "WithWorkspaceDiagnostic",
    "capabilities",
]
