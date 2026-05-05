#!/bin/bash
# Pause/Resume Speaking Script
# Toggles pause state of TTS audio playback

# Toggle pause on mpg123 (primary player)
if pgrep -x mpg123 > /dev/null; then
    # Check if process is stopped (T status)
    if ps -o state= -p $(pgrep -x mpg123) | grep -q "T"; then
        pkill -CONT mpg123
        echo "Resumed mpg123"
    else
        pkill -STOP mpg123
        echo "Paused mpg123"
    fi
    exit 0
fi

# Toggle pause on VLC
if pgrep -x vlc > /dev/null || pgrep -f cvlc > /dev/null; then
    PNAME=$(pgrep -x vlc || pgrep -f cvlc | head -n 1)
    if ps -o state= -p $PNAME | grep -q "T"; then
        pkill -CONT -f vlc
        echo "Resumed vlc"
    else
        pkill -STOP -f vlc
        echo "Paused vlc"
    fi
    exit 0
fi

# Toggle pause on paplay (PulseAudio)
if pgrep -x paplay > /dev/null; then
    if ps -o state= -p $(pgrep -x paplay) | grep -q "T"; then
        pkill -CONT paplay
    else
        pkill -STOP paplay
    fi
    exit 0
fi

# Toggle pause on ffplay
if pgrep -x ffplay > /dev/null; then
    if ps -o state= -p $(pgrep -x ffplay) | grep -q "T"; then
        pkill -CONT ffplay
    else
        pkill -STOP ffplay
    fi
    exit 0
fi

echo "No active TTS playback to pause/resume"
