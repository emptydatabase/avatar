import asyncio
import dataclasses
import inspect
import logging
import threading
from abc import ABC
from asyncio import Task, CancelledError
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass, field
from functools import singledispatchmethod
from types import TracebackType
from typing import TypedDict, NotRequired, Any

from .messages import Message


class NodeConfig(TypedDict):
    cls: str
    kwargs: NotRequired[dict[str, Any]]


nodes_registry: dict[str, type[Node]] = {}
name_counters: dict[str, int] = {}


def get_node_type(name: str) -> type[Node]:
    return nodes_registry[name]


def next_node_name(node_type: type) -> str:
    base_name = node_type.__name__
    if counter := name_counters.get(base_name):
        name_counters[base_name] += 1
        return f"{base_name}-{counter}"
    else:
        name_counters[base_name] = 1
        return base_name


def dummy_pool_send(message: Message):
    return asyncio.create_task(asyncio.sleep(0))


@dataclass
class Node(ABC):
    _: dataclasses.KW_ONLY
    name: str = field(default="__no_name__")

    def __init_subclass__(cls):
        if not inspect.isabstract(cls):
            nodes_registry[cls.__name__] = cls

    def __post_init__(self):
        if self.name == "__no_name__":
            self.name = next_node_name(type(self))
        self.logger = logging.getLogger(self.name)
        self.pool_send = dummy_pool_send

    async def __aenter__(self):
        self.logger.info("START")
        self.loop = asyncio.get_running_loop()
        return self

    async def run(self):
        ...

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None):
        self.logger.info("STOP")

    @singledispatchmethod
    async def accept(self, message: Message):
        ...

    def send(self, message: Message) -> Task:
        if message.log:
            self.logger.info(f"SEND: {message}")
        return self.pool_send(message)

    def get_config(self) -> NodeConfig:
        return NodeConfig(
            cls=type(self).__name__,
            kwargs=dataclasses.asdict(self)
        )


@dataclass
class ThreadNode(Node, ABC):
    async def __aenter__(self):
        self._closing = threading.Event()
        return await super().__aenter__()

    def is_running(self):
        return not self._closing.is_set()

    async def run(self):
        self._task = asyncio.create_task(asyncio.to_thread(self.thread))
        await self._task

    def thread(self):
        ...

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None):
        self._closing.set()
        with suppress(CancelledError):
            await self._task
        return await super().__aexit__(exc_type, exc_val, exc_tb)

    def send_threadsafe(self, message: Message):
        return self.loop.call_soon_threadsafe(self.send, message)


def node(function: Callable[[Node], ...]) -> type[Node]:
    if inspect.iscoroutinefunction(function):
        return type(function.__name__, (Node,), {
            "run": function
        })
    else:
        return type(function.__name__, (ThreadNode,), {
            "thread": function
        })
