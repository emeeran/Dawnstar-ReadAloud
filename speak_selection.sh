#!/bin/bash
# Cross-platform clipboard to TTS
# Supports: Linux (X11/Wayland), macOS, Windows (via WSL)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TTS_APP="$SCRIPT_DIR/tts"

# Get clipboard text using Python helper (delegates to platform.py)
TEXT=$("$TTS_APP" --get-clipboard 2>/dev/null)

if [ -z "$TEXT" ]; then
    # Cross-platform notification (optional, silent fail if not available)
    if command -v notify-send &> /dev/null; then
        notify-send "TTS" "No text selected" 2>/dev/null
    fi
    exit 1
fi

# Send notification
if command -v notify-send &> /dev/null; then
    notify-send "Speaking Selection" "Processing text..." -t 2000 2>/dev/null
fi

# Run TTS application through stdin
echo "$TEXT" | "$TTS_APP" -
