from dataclasses import dataclass
from functools import singledispatchmethod
from types import TracebackType
from typing import Any

import pygame

from ..defaults import FACE_FONT, FACE_CAPTION
from ..messages import TranscriptionPartial, StopTalking, Message, TranscriptionResult, Speaking, SpeakingEnd
from ..node import Node
from ..sprites import STANDING, TALKING, THINKING, JOY

colors = {
    "black": (0, 0, 0),
    "blue": (50, 50, 255)
}


@dataclass
class Video(Node):
    font: str = FACE_FONT
    caption: str = FACE_CAPTION

    async def __aenter__(self):
        pygame.init()
        self._sys_font = pygame.font.SysFont(self.font, 30)
        self._joy = pygame.image.load(JOY)
        self._talking = pygame.image.load(TALKING)
        self._thinking = pygame.image.load(THINKING)
        self._standing = pygame.image.load(STANDING)
        self._screen = pygame.display.set_mode((512, 512))
        pygame.display.set_caption(self.caption)
        self.show(self._joy)
        return await super().__aenter__()

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None):
        pygame.quit()
        return await super().__aexit__(exc_type, exc_val, exc_tb)

    def show(
            self, sprite: Any,
            text: str | None = None,
            color: str | None = None
    ):
        rect = sprite.get_rect()
        self._screen.blit(sprite, rect)
        if text:
            surface = self._sys_font.render(
                text, False, colors[color or "black"]
            )
            self._screen.blit(surface, (25, 25))
        pygame.display.flip()

    @singledispatchmethod
    async def accept(self, message: Message):
        ...

    @accept.register
    async def _(self, message: TranscriptionPartial):
        self.show(self._standing, message.data, "black")

    @accept.register
    async def _(self, message: TranscriptionResult):
        self.show(self._thinking, message.data, "black")

    @accept.register
    async def _(self, message: Speaking):
        self.show(self._talking, message.data, "blue")

    @accept.register
    async def _(self, message: StopTalking | SpeakingEnd):
        self.show(self._standing)
