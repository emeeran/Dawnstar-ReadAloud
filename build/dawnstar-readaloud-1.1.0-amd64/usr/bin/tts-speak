#!/bin/bash
# Speak from cursor position to end of document.
# Uses accessibility APIs to get text without scrolling.
# Shows current sentence in notification.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TTS_APP="$SCRIPT_DIR/tts"
ACCESSIBLE_SCRIPT="$SCRIPT_DIR/get_accessible_text.py"
STATE_DIR="/tmp/tts_cursor_state"
SENTENCE_FILE="$STATE_DIR/current_sentence.txt"

# Initialize state directory
mkdir -p "$STATE_DIR"
rm -f "$SENTENCE_FILE"

# Function to show notification
notify() {
    if command -v notify-send &> /dev/null; then
        notify-send "TTS" "$1" -t 2000
    fi
}

# Try to get text via accessibility APIs (no scrolling!)
# This gets selected text first, then falls back to cursor position
TEXT=""
METHOD=""

if [ -x "$ACCESSIBLE_SCRIPT" ]; then
    TEXT=$(python3 "$ACCESSIBLE_SCRIPT" 2>/dev/null)
    if [ -n "$TEXT" ]; then
        METHOD="accessibility"
    fi
fi

if [ -z "$TEXT" ]; then
    notify "No text found. Select text or place cursor in a text area."
    exit 1
fi

# Save text to temp file
TEMP_FILE=$(mktemp /tmp/tts_cursor_XXXXXX.txt)
echo "$TEXT" > "$TEMP_FILE"

# Launch TTS with sentence tracking
(
    "$TTS_APP" --sentence-file "$SENTENCE_FILE" "$TEMP_FILE" > /dev/null 2>&1
    rm -f "$TEMP_FILE"
    rm -f "$SENTENCE_FILE"
) & disown

# Monitor sentence file and show notification with current sentence
if command -v notify-send &> /dev/null; then
    (
        LAST_SENTENCE=""
        while [ ! -f "$SENTENCE_FILE" ]; do
            sleep 0.1
            if ! pgrep -f "tts.*$TEMP_FILE" > /dev/null 2>&1 && [ ! -f "$TEMP_FILE" ]; then
                exit 0
            fi
        done

        while [ -f "$SENTENCE_FILE" ] || pgrep -f "tts.*sentence-file" > /dev/null 2>&1; do
            if [ -f "$SENTENCE_FILE" ]; then
                CURRENT=$(cat "$SENTENCE_FILE" 2>/dev/null)
                if [ -n "$CURRENT" ] && [ "$CURRENT" != "$LAST_SENTENCE" ]; then
                    LAST_SENTENCE="$CURRENT"
                    notify-send "TTS Speaking" "${CURRENT:0:100}$([ ${#CURRENT} -gt 100 ] && echo '...')" -t 5000 -r 12345
                fi
            fi
            sleep 0.2
        done

        notify-send "TTS" "Finished speaking" -t 1500 -r 12345
    ) & disown
fi
