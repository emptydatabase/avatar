import asyncio
import json
from asyncio import Task
from dataclasses import dataclass, field
from functools import singledispatchmethod
from types import TracebackType
from typing import Literal

from aiohttp import ClientSession

from ..defaults import LANGUAGE, OLLAMA_URL
from ..messages import TranscriptionResult, TranscriptionPartial, AssistantSaid, Say, Generating, Message, StopTalking, \
    SpeakingEnd
from ..node import Node
from ..prompts import default_prompts


class OllamaException(Exception):
    def __init__(self, message: str):
        self.message = message


@dataclass
class Agent(Node):
    ollama_model: str
    ollama_url: str = OLLAMA_URL
    system_prompt: str | None = None
    messages: list[dict] = field(default_factory=list)
    lang: str = LANGUAGE

    async def __aenter__(self):
        self.gen_tasks: list[Task] = []
        if len(self.messages) == 0:
            self.messages.append({
                "role": "system",
                "content": self.system_prompt or default_prompts[self.lang]
            })
        return await super().__aenter__()

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None):
        await self.stop_generating()
        return await super().__aexit__(exc_type, exc_val, exc_tb)

    @singledispatchmethod
    async def accept(self, message: Message):
        ...

    @accept.register
    async def _(self, message: TranscriptionResult):
        await self.stop_generating()
        if text := message.data:
            self.append_message(
                role="user",
                content=text
            )
            await self.generate()

    @accept.register
    async def _(self, message: TranscriptionPartial):
        if message.data:
            await self.stop_generating()

    @accept.register
    async def _(self, message: AssistantSaid):
        if text := message.data:
            self.append_message(
                role="assistant",
                content=text
            )

    async def stop_generating(self):
        if len(self.gen_tasks) > 0:
            for task in self.gen_tasks:
                task.cancel()
            await self.send(StopTalking())

    async def generate(self):
        current = asyncio.current_task()
        if not current:
            raise RuntimeError
        self.gen_tasks.append(current)
        sub_tasks: list[Task] = []

        def cleanup(t: Task):
            self.gen_tasks.remove(t)
            for task in sub_tasks:
                if not task.done():
                    task.cancel()

        current.add_done_callback(cleanup)
        self.send(Generating(f"From {len(self.messages)} messages"))

        async with (
            ClientSession() as session,
            session.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.ollama_model,
                    "messages": self.messages,
                    "think": False,
                }
            ) as response
        ):
            buffer = ""
            async for line in response.content:
                packet = json.loads(line)
                if packet.get("done", False):
                    break
                elif error := packet.get("error"):
                    raise OllamaException(error)

                buffer += packet["message"]["content"]
                *sendable, buffer = buffer.split("\n")
                for s in sendable:
                    if s:
                        sub_tasks.append(self.send(Say(s)))
            if buffer:
                sub_tasks.append(self.send(Say(buffer)))

        await asyncio.gather(*sub_tasks)
        await self.send(SpeakingEnd())

    def append_message(
            self,
            role: Literal["assistant", "user"],
            content: str
    ):
        last_message = self.messages[-1]
        if last_message["role"] == role:
            last_message["content"] += "\n" + content
        else:
            self.messages.append({
                "role": role,
                "content": content
            })
