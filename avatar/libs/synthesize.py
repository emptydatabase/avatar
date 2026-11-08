from io import BytesIO

from gtts import gTTS
from mutagen.mp3 import MP3


def synthesize(text: str, lang: str) -> tuple[BytesIO, float]:
    buffer = BytesIO()
    gTTS(text, lang=lang).write_to_fp(buffer)
    buffer.seek(0)
    length = MP3(buffer).info.length
    buffer.seek(0)
    return buffer, length
