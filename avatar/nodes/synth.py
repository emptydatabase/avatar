import asyncio
import asyncio.subprocess
import time
from asyncio import CancelledError, Lock, Task
from dataclasses import dataclass
from functools import singledispatchmethod
from types import TracebackType

from ..defaults import MPV_COMMAND, LANGUAGE
from ..libs import synthesize
from ..messages import Say, AssistantSaid, Message, Speaking, StopTalking
from ..node import Node


@dataclass
class Synth(Node):
    mpv_command: str = MPV_COMMAND
    lang: str = LANGUAGE

    async def __aenter__(self):
        self._lock = Lock()
        self._players: list[Task] = []
        await self.start_mpv()
        return await super().__aenter__()

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None):
        self.stop_mpv()
        return await super().__aexit__(exc_type, exc_val, exc_tb)

    def is_talking(self):
        return self._lock.locked()

    @singledispatchmethod
    async def accept(self, message: Message):
        ...

    @accept.register
    async def _(self, message: Say):
        text = message.data
        if not text:
            return
        current = asyncio.current_task()
        if current is None:
            raise RuntimeError
        self._players.append(current)
        current.add_done_callback(self._players.remove)
        buffer, length = await asyncio.to_thread(synthesize, text, self.lang)
        self.stdin.write(buffer.read())
        async with self._lock:
            start = time.monotonic()
            self.send(Speaking(text))
            try:
                await asyncio.sleep(length)
            except CancelledError:
                await self.reset_mpv()
        end = time.monotonic()
        done = end - start
        if done >= length:
            said = text
        else:
            n = int(len(text) * done / length)
            said = text[:n]
        if said:
            await self.send(AssistantSaid(said))

    @accept.register
    async def _(self, message: StopTalking):
        if self.is_talking():
            await self.reset_mpv()

    async def start_mpv(self):
        self.process = await asyncio.create_subprocess_exec(
            *self.mpv_command.split(),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.DEVNULL,
        )
        stdin = self.process.stdin
        if stdin:
            self.stdin = stdin
        else:
            raise RuntimeError

    async def reset_mpv(self):
        self.stop_mpv()
        await self.start_mpv()

    def stop_mpv(self):
        current = asyncio.current_task()
        for task in self._players:
            if task is not current:
                task.cancel()
        self.process.terminate()
