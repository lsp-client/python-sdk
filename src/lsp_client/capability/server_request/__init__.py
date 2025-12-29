from __future__ import annotations

from typing import Final

from ..diagnostic.workspace import WithWorkspaceDiagnostic
from .configuration import WithRespondConfigurationRequest
from .inlay_hint_refresh import WithRespondInlayHintRefresh
from .show_document_request import WithRespondShowDocumentRequest
from .show_message_request import WithRespondShowMessageRequest
from .workspace_folders import WithRespondWorkspaceFoldersRequest

capabilities: Final = (
    WithRespondConfigurationRequest,
    WithWorkspaceDiagnostic,
    WithRespondInlayHintRefresh,
    WithRespondShowDocumentRequest,
    WithRespondShowMessageRequest,
    WithRespondWorkspaceFoldersRequest,
)

__all__ = [
    "WithRespondConfigurationRequest",
    "WithRespondInlayHintRefresh",
    "WithRespondShowDocumentRequest",
    "WithRespondShowMessageRequest",
    "WithRespondWorkspaceFoldersRequest",
    "WithWorkspaceDiagnostic",
    "capabilities",
]
