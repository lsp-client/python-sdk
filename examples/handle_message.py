from __future__ import annotations

from typing import override

import anyio

import lsp_client
from lsp_client import lsp_type
from lsp_client.clients.pyrefly import PyreflyClient

lsp_client.enable_logging()


class CustomClient(PyreflyClient):
    @override
    async def receive_log_message(self, noti: lsp_type.LogMessageNotification) -> None:
        print(f"✨ Log Message: {noti.params.message}")


async def main() -> None:
    async with CustomClient() as client:
        print(client)


if __name__ == "__main__":
    anyio.run(main)
