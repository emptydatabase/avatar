import logging
import os

from dotenv import load_dotenv

from avatar import run_pool
from avatar.nodes import Record

load_dotenv()

logging.basicConfig(level=logging.INFO)


run_pool([
    Record(vosk_path=os.environ["VOSK_PATH"]),
], run_forever=True)
