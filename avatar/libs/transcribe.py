import json

import pyaudio
import vosk
from vosk import Model, KaldiRecognizer

vosk.SetLogLevel(-1)


def pyaudio_input_stream(
    rate: int,
    format: int,
    channels: int,
    frames_per_buffer: int,
):
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=format,
        channels=channels,
        rate=rate,
        input=True,
        frames_per_buffer=frames_per_buffer
    )

    try:
        while True:
            yield stream.read(frames_per_buffer)
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()


def transcribe(
        path: str,
        rate: int,
        format: int,
        channels: int,
        frames_per_buffer: int,
):
    model = Model(path)
    rec = KaldiRecognizer(model, rate)

    for data in pyaudio_input_stream(
        format=format,
        channels=channels,
        rate=rate,
        frames_per_buffer=frames_per_buffer
    ):
        if rec.AcceptWaveform(data):
            response = rec.Result()
        else:
            response = rec.PartialResult()
        yield json.loads(response)
