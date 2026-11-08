import asyncio
import logging

from dotenv import load_dotenv

from avatar import run_pool, node, Node
from avatar.messages import TranscriptionPartial, TranscriptionResult, Speaking
from avatar.nodes import Video

load_dotenv()

logging.basicConfig(level=logging.INFO)


@node
async def debug(self: Node):
    await asyncio.sleep(2)

    async def transcription(text: str):
        buffer = []
        for word in text.split():
            buffer.append(word)
            self.send(TranscriptionPartial(" ".join(buffer)))
            await asyncio.sleep(0.5)
        TranscriptionResult(" ".join(buffer))

    await transcription("Ciao come stai?")
    await asyncio.sleep(1)
    self.send(Speaking("Tutto bene e tu?"))
    await asyncio.sleep(2)



run_pool([
    debug(),
    Video()
])
