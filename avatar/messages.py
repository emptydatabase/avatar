class Message:
    log = True

    def __str__(self) -> str:
        return f"{type(self).__name__}"


class Packet[T](Message):
    def __init__(self, data: T):
        self.data = data

    def __str__(self) -> str:
        return f"{type(self).__name__}: {self.data}"


class Recording(Message):
    ...


class TranscriptionResult(Packet[str]):
    ...


class TranscriptionPartial(Packet[str]):
    def __init__(self, data: str):
        super().__init__(data)
        self.log = data.strip() != ""


class Generating(Packet[str]):
    ...


class Say(Packet[str]):
    ...


class StopTalking(Message):
    ...


class Speaking(Packet[str]):
    ...


class SpeakingEnd(Message):
    ...


class AssistantSaid(Packet[str]):
    ...
