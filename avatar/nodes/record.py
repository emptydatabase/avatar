from dataclasses import dataclass

from ..defaults import AUDIO_RATE, AUDIO_FORMAT, AUDIO_CHANNELS, AUDIO_CHUNK_SIZE, LANGUAGE
from ..libs import transcribe
from ..messages import TranscriptionResult, TranscriptionPartial, Recording
from ..node import ThreadNode


@dataclass
class Record(ThreadNode):
    vosk_path: str
    audio_rate: int = AUDIO_RATE
    audio_format: int = AUDIO_FORMAT
    audio_channels: int = AUDIO_CHANNELS
    audio_chunk_size: int = AUDIO_CHUNK_SIZE
    lang: str = LANGUAGE

    def thread(self):
        transcriber = transcribe(
            path=self.vosk_path,
            format=self.audio_format,
            channels=self.audio_channels,
            rate=self.audio_rate,
            frames_per_buffer=self.audio_chunk_size
        )
        item = next(transcriber)
        self.send_threadsafe(Recording())
        while self.is_running():
            if text := item.get("text"):
                self.send_threadsafe(TranscriptionResult(text))
            elif partial := item.get("partial"):
                self.send_threadsafe(TranscriptionPartial(partial))
            item = next(transcriber)
