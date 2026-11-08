#!/usr/bin/env sh

pactl load-module module-null-sink sink_name=InputSpeaker sink_properties=device.description=InputSpeaker
pactl load-module module-null-sink media.class=Audio/Source/Virtual sink_name=InputMic channel_map=front-left,front-right

pactl load-module module-null-sink sink_name=OutputSpeaker sink_properties=device.description=OutputSpeaker
pactl load-module module-null-sink media.class=Audio/Source/Virtual sink_name=OutputMic channel_map=front-left,front-right

sleep 1

pw-link InputSpeaker:monitor_FL InputMic:input_FL
pw-link InputSpeaker:monitor_FR InputMic:input_FR

pw-link OutputSpeaker:monitor_FL OutputMic:input_FL
pw-link OutputSpeaker:monitor_FR OutputMic:input_FR
