from __future__ import annotations

import json
from typing import Any, cast

from lsprotocol import converters

from lsp_client.utils.types import Notification, Request, Response, lsp_type

from .exception import JsonRpcParseError, JsonRpcResponseError
from .types import (
    RawNotification,
    RawPackage,
    RawRequest,
    RawRequestPackage,
    RawResponsePackage,
)

converter = converters.get_converter()


@converter.register_structure_hook
def _(
    object_: Any, _: object
) -> (
    str
    | lsp_type.NotebookDocumentFilterNotebookType
    | lsp_type.NotebookDocumentFilterScheme
    | lsp_type.NotebookDocumentFilterPattern
    | None
):
    """HACK patch from <https://github.com/microsoft/lsprotocol/issues/430#issuecomment-3582108388> for `lsprotocol` bug"""

    if object_ is None:
        return None
    if isinstance(object_, str):
        return str(object_)
    if "notebookType" in object_:
        return converter.structure(object_, lsp_type.NotebookDocumentFilterNotebookType)
    if "scheme" in object_:
        return converter.structure(object_, lsp_type.NotebookDocumentFilterScheme)
    return converter.structure(object_, lsp_type.NotebookDocumentFilterPattern)


def value_deserialize[R](raw_value: Any, schema: type[R]) -> R:
    return converter.structure(raw_value, schema)


def value_serialize(value: Any) -> Any:
    return converter.unstructure(value)


def package_serialize(package: RawPackage) -> str:
    return json.dumps(package)


def request_deserialize[R](raw_req: RawRequestPackage, schema: type[R]) -> R:
    return converter.structure(raw_req, schema)


def request_serialize(request: Request) -> RawRequest:
    return cast(RawRequest, converter.unstructure(request))


def notification_serialize(notification: Notification) -> RawNotification:
    return cast(RawNotification, converter.unstructure(notification))


def response_deserialize[R](
    raw_resp: RawResponsePackage, schema: type[Response[R]]
) -> R:
    """Deserialize a JSON-RPC response package. Raise `ValueError` if the response is an error."""

    match raw_resp:
        case {"error": _} as raw_err_resp:
            err_resp = converter.structure(raw_err_resp, lsp_type.ResponseErrorMessage)
            if err := err_resp.error:
                raise JsonRpcResponseError(err.code, err.message, err.data)
            raise JsonRpcParseError(f"Invalid Error Response: {err_resp}")
        case {"result": _} as raw_resp:
            resp = converter.structure(raw_resp, schema)
            return resp.result
        case unexpected:
            raise JsonRpcParseError(f"Unexpected response: {unexpected}")


def response_serialize(response: Response[Any]) -> RawResponsePackage:
    return cast(RawResponsePackage, converter.unstructure(response))
