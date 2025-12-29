from __future__ import annotations

from typing import Literal

from lsp_client.jsonrpc.channel import RespSender
from lsp_client.jsonrpc.types import RawNotification, RawRequest

type ServerRequest = tuple[RawRequest, RespSender] | RawNotification

type ServerType = Literal["local", "container", "socket"]
