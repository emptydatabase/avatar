import logging

from avatar import run_pool, node, Node
from avatar.messages import TranscriptionResult
from avatar.nodes import Mock

logging.basicConfig(level=logging.INFO)


@node
async def debug(self: Node):
    self.send(TranscriptionResult("DEBUG TEST"))


run_pool([
    debug(),
    Mock(
        mock_agent=True,
        mock_synth=True,
    ),
])
