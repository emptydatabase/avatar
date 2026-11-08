# Avatar

A proof-of-concept conversational AI agent.

## Installation

```
git clone https://www.github.com/emptydatabase/avatar
cd avatar
pip install -r requirements.txt
```

### External requirements

- [Vosk model](https://alphacephei.com/vosk/models): For speech recognition
- [Ollama](https://ollama.com/): Model backend
- [Pulseaudio](https://www.freedesktop.org/wiki/Software/PulseAudio/) (optional): To connect to virtual audio devices
- [OBS Studio](https://obsproject.com/) (optional, with the kernel module `v4l2loopback`): To connect to a virtual webcam

## How to connect to an external program

1. Run `sh scripts/pulse.sh` to create virtual audio devices
2. Open OBS Studio
3. Run `python main.py` and wait until you can see the pygame window (ignore error messages)
4. Start a OBS virtual webcam connected to the pygame window
5. Open your target program (for example a browser connected to a Zoom call)
6. Use `pavucontrol` to:
   - Set the browser playback device to `InputSpeaker`
   - Set the browser recording device to `OutputMic`
   - Set the `main.py` playback device to `OutputSpeaker` (it will appear only while the agent is talking)
   - Set the `main.py` recording device to `InputMic`
7. Talk with the agent through the video call
