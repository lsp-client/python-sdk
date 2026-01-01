from __future__ import annotations

from collections.abc import Iterable
from typing import Any, TypeGuard

from lsp_client.utils.types import lsp_type


def is_locations(result: Any) -> TypeGuard[Iterable[lsp_type.Location]]:
    return result is not None and all(
        isinstance(item, lsp_type.Location) for item in result
    )


def is_definition_links(result: Any) -> TypeGuard[Iterable[lsp_type.DefinitionLink]]:
    return result is not None and all(
        isinstance(item, lsp_type.LocationLink) for item in result
    )


def is_location_links(result: Any) -> TypeGuard[Iterable[lsp_type.LocationLink]]:
    return result is not None and all(
        isinstance(item, lsp_type.LocationLink) for item in result
    )


def is_workspace_symbols(result: Any) -> TypeGuard[Iterable[lsp_type.WorkspaceSymbol]]:
    return result is not None and all(
        isinstance(item, lsp_type.WorkspaceSymbol) for item in result
    )


def is_document_symbols(result: Any) -> TypeGuard[Iterable[lsp_type.DocumentSymbol]]:
    return result is not None and all(
        isinstance(item, lsp_type.DocumentSymbol) for item in result
    )


def is_symbol_information_seq(
    result: Any,
) -> TypeGuard[Iterable[lsp_type.SymbolInformation]]:
    return result is not None and all(
        isinstance(item, lsp_type.SymbolInformation) for item in result
    )


def is_completion_items(result: Any) -> TypeGuard[Iterable[lsp_type.CompletionItem]]:
    return result is not None and all(
        isinstance(item, lsp_type.CompletionItem) for item in result
    )


def is_code_actions(
    result: Any,
) -> TypeGuard[Iterable[lsp_type.Command | lsp_type.CodeAction]]:
    return result is not None and all(
        isinstance(item, lsp_type.Command | lsp_type.CodeAction) for item in result
    )
