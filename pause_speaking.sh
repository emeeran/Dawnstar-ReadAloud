#!/bin/bash
# Pause/Resume Speaking Script
# Toggles pause state of TTS audio playback

# Toggle pause on mpg123 (primary player)
if pgrep -x mpg123 > /dev/null; then
    pkill -STOP mpg123 2>/dev/null || pkill -CONT mpg123 2>/dev/null
    exit 0
fi

# Toggle pause on VLC
if pgrep -x vlc > /dev/null || pgrep -f cvlc > /dev/null; then
    pkill -STOP vlc 2>/dev/null || pkill -CONT vlc 2>/dev/null
    pkill -STOP cvlc 2>/dev/null || pkill -CONT cvlc 2>/dev/null
    exit 0
fi

# Toggle pause on paplay (PulseAudio)
if pgrep -x paplay > /dev/null; then
    pkill -STOP paplay 2>/dev/null || pkill -CONT paplay 2>/dev/null
    exit 0
fi

# Toggle pause on ffplay
if pgrep -x ffplay > /dev/null; then
    pkill -STOP ffplay 2>/dev/null || pkill -CONT ffplay 2>/dev/null
    exit 0
fi

echo "No active TTS playback to pause/resume"
