import logging
import os
from dataclasses import dataclass
from functools import singledispatchmethod

from dotenv import load_dotenv

from avatar import run_pool, Node
from avatar.messages import TranscriptionResult, Message, Say, AssistantSaid
from avatar.nodes import Agent

load_dotenv()

logging.basicConfig(level=logging.INFO)


@dataclass
class Debug(Node):
    async def __aenter__(self):
        result = await super().__aenter__()
        self.future = self.loop.create_future()
        return result

    async def run(self):
        self.send(TranscriptionResult("Ciao! Raccontami una storia"))
        await self.future
        self.send(TranscriptionResult("Non mi interessa. Dimmi il tuo nome."))

    @singledispatchmethod
    async def accept(self, message: Message):
        ...

    @accept.register
    async def _(self, message: Say):
        if self.future.done():
            return
        text = message.data
        self.send(AssistantSaid(text[:len(text) // 2]))
        self.future.set_result(None)


run_pool([
    Debug(),
    Agent(ollama_model=os.environ["OLLAMA_MODEL"]),
])
