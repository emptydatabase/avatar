import asyncio
import logging

from dotenv import load_dotenv

from avatar import run_pool, node, Node
from avatar.messages import Say, StopTalking
from avatar.nodes import Synth

load_dotenv()

logging.basicConfig(level=logging.INFO)


@node
async def debug(self: Node):
    self.send(Say("Ciao! come stai? Che mi racconti oggi?"))
    await asyncio.sleep(2.5)
    await self.send(StopTalking())
    await self.send(Say("Scusa hai detto qualcosa?"))


run_pool([
    debug(),
    Synth(),
])
