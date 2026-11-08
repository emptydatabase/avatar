from dataclasses import dataclass
from functools import singledispatchmethod

from ..messages import Say, AssistantSaid, TranscriptionResult, Message
from ..node import Node


@dataclass
class Mock(Node):
    mock_agent: bool = False
    mock_synth: bool = False

    @singledispatchmethod
    async def accept(self, message: Message):
        ...

    @accept.register
    async def _(self, message: TranscriptionResult):
        if self.mock_agent:
            await self.send(Say(message.data))

    @accept.register
    async def _(self, message: Say):
        if self.mock_synth:
            await self.send(AssistantSaid(message.data))
