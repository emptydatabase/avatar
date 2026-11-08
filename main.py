import logging
import os

from dotenv import load_dotenv

from avatar import run_pool
from avatar.nodes import Video, Record, Agent, Synth

load_dotenv()

logging.basicConfig(level=logging.INFO)

run_pool([
    Record(vosk_path=os.environ["VOSK_PATH"]),
    Agent(ollama_model=os.environ["OLLAMA_MODEL"]),
    Synth(),
    Video(),
])
