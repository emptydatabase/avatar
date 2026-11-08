import asyncio
import logging
from asyncio import Task, CancelledError, Future
from collections.abc import Coroutine
from contextlib import suppress, AsyncExitStack
from types import TracebackType
from typing import TypedDict, Any, NotRequired

from .messages import Message
from .node import Node, NodeConfig


class PoolClosed(Exception):
    pass


class NodeNameTaken(Exception):
    pass


class PoolConfig(TypedDict):
    nodes: NotRequired[dict[str, NodeConfig]]


def run_pool(nodes: list[Node], run_forever: bool = False):
    async def main():
        async with Pool(nodes) as pool:
            if run_forever:
                async def sleep_forever():
                    await asyncio.get_running_loop().create_future()
                pool.create_task(sleep_forever())

            await pool.wait()
    return asyncio.run(main())


class Pool:
    def __init__(self, nodes: list[Node]):
        self._nodes = {
            node.name: node
            for node in nodes
        }

        for node in self._nodes.values():
            node.pool_send = self.send

        self.futures: set[Future] = set()
        self._closing = False
        self.logger = logging.getLogger("pool")

    async def __aenter__(self):
        self._exit_stack = AsyncExitStack()
        await self._exit_stack.__aenter__()

        for node in self._nodes.values():
            await self._exit_stack.enter_async_context(node)

        for node in self._nodes.values():
            self.create_task(node.run())

        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None):
        self._closing = True
        suppressed = await self._exit_stack.__aexit__(exc_type, exc_val, exc_tb)
        return suppressed or (exc_type and issubclass(exc_type, CancelledError))

    async def wait(self):
        while len(self.futures) > 0:
            try:
                await asyncio.gather(*self.futures, return_exceptions=True)
            except CancelledError:
                for future in self.futures:
                    future.cancel()

    def send(self, message: Message) -> Task:
        if self._closing:
            raise PoolClosed

        async def gather():
            await asyncio.gather(*(
                node.accept(message)
                for node in self._nodes.values()
            ))

        return self.create_task(gather())

    def get_config(self) -> PoolConfig:
        return PoolConfig(
            nodes={
                name: node.get_config()
                for name, node in self._nodes.items()
            },
        )

    def get_node_config(self, name: str) -> NodeConfig | None:
        if node := self._nodes.get(name):
            return node.get_config()
        else:
            return None

    def create_task[T](self, coro: Coroutine[Any, Any, T]) -> Task[T]:
        task = asyncio.create_task(coro)
        self.futures.add(task)
        task.add_done_callback(self._done_callback)
        return task

    def _done_callback(self, task: Task):
        with suppress(KeyError):
            self.futures.remove(task)
