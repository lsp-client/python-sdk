from __future__ import annotations

from collections.abc import AsyncGenerator, Hashable
from contextlib import asynccontextmanager
from typing import NamedTuple, Self

import anyio
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from attrs import Factory, define, frozen


@frozen
class OneShotSender[T]:
    sender: MemoryObjectSendStream[T]

    def send(self, item: T) -> None:
        self.sender.send_nowait(item)


@frozen
class OneShotReceiver[T]:
    receiver: MemoryObjectReceiveStream[T]

    async def receive(self) -> T:
        item = await self.receiver.receive()
        self.receiver.close()
        return item

    def try_receive(self) -> T | None:
        item = self.receiver.receive_nowait()
        self.receiver.close()
        return item


class oneshot_channel[T](NamedTuple):
    sender: OneShotSender[T]
    receiver: OneShotReceiver[T]

    @classmethod
    def create(cls) -> Self:
        sender, receiver = anyio.create_memory_object_stream[T]()
        return cls(
            sender=OneShotSender(sender),
            receiver=OneShotReceiver(receiver),
        )


@define
class OneShotTable[T]:
    """Dispatch data to one-shot senders by ID."""

    _pending: dict[Hashable, OneShotSender[T]] = Factory(dict)
    """wait for `_pending` to be empty."""

    def send(self, id: Hashable, data: T) -> None:
        if id not in self._pending:
            raise ValueError(f"Pending request of id {id} not found")

        self._pending[id].send(data)
        self._pending.pop(id)

    async def receive(self, id: Hashable) -> T:
        if id in self._pending:
            raise ValueError(f"Sender with id {id} already registered")

        tx, rx = oneshot_channel.create()
        try:
            self._pending[id] = tx
            return await rx.receive()
        finally:
            self._pending.pop(id, None)

    @property
    def completed(self) -> bool:
        return not self._pending


type Sender[T] = MemoryObjectSendStream[T]
type Receiver[T] = MemoryObjectReceiveStream[T]


class channel[T](NamedTuple):
    sender: Sender[T]
    receiver: Receiver[T]

    @classmethod
    @asynccontextmanager
    async def create(
        cls, max_buffer_size: int = 128
    ) -> AsyncGenerator[channel[T]]:  # ty can't resolve `Self` here
        sender, receiver = anyio.create_memory_object_stream[T](max_buffer_size)
        async with sender, receiver:
            yield cls(sender=sender, receiver=receiver)
