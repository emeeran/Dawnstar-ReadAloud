#!/bin/bash
# Stop Speaking Script
# Kills all TTS-related processes

# 1. INSTANT SILENCE (PulseAudio)
# Mute/Kill the audio stream directly at the sink
if command -v pactl &> /dev/null; then
  # List all sink inputs and kill them? Or just mute?
  # Safest instant mute:
  pactl list sink-inputs short | grep -iE 'mp3|mpg123|vlc|player' | cut -f1 | xargs -r -n1 pactl kill-sink-input
fi

# 2. Kill Docker Wrapper
pkill -f "tts-docker"

# 3. Kill Docker Containers (Robust Label Match)
docker ps -q --filter label=app=enhanced-tts | xargs -r docker kill
# Legacy fallback (image name)
docker ps -q --filter ancestor=enhanced-tts:latest | xargs -r docker kill

# 4. Cleanup local processes
pkill -f "python.*app.py"
pkill -f edge-tts
pkill -f mpg123
