#!/bin/bash
# Speak text from cursor position in the focused application.
#
# Priority:
#   1. Accessibility APIs (AT-SPI) → text from cursor to end of document
#   2. Primary selection (highlighted text) → via xclip
#
# Shortcut: Ctrl+Alt+F

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TTS_APP="$SCRIPT_DIR/tts"
ACCESSIBLE_SCRIPT="$SCRIPT_DIR/get_accessible_text.py"
STATE_DIR="/tmp/tts_cursor_state"
SENTENCE_FILE="$STATE_DIR/current_sentence.txt"

# Initialize state directory
mkdir -p "$STATE_DIR"
rm -f "$SENTENCE_FILE"

notify() {
    if command -v notify-send &> /dev/null; then
        notify-send "TTS" "$1" -t 2000 2>/dev/null
    fi
}

echo "$(date) - speak_from_cursor: starting" >> /tmp/tts_debug.log

TEXT=""
METHOD=""

# ── Strategy 1: Accessibility APIs (speak from cursor to end) ──
if [ -f "$ACCESSIBLE_SCRIPT" ]; then
    TEXT=$(python3 "$ACCESSIBLE_SCRIPT" 2>/dev/null)
    if [ -n "$TEXT" ]; then
        METHOD="accessibility"
        echo "$(date) - Got text via accessibility (${#TEXT} chars)" >> /tmp/tts_debug.log
    fi
fi

# ── Strategy 2: Primary selection (highlighted text) ──
if [ -z "$TEXT" ]; then
    if command -v xclip &> /dev/null; then
        TEXT=$(xclip -o -selection primary 2>/dev/null)
        if [ -n "$TEXT" ]; then
            METHOD="primary-selection"
            echo "$(date) - Got text via primary selection (${#TEXT} chars)" >> /tmp/tts_debug.log
        fi
    fi
fi

if [ -z "$TEXT" ]; then
    notify "No text at cursor. Place cursor in a text area or highlight text."
    echo "$(date) - speak_from_cursor: no text found" >> /tmp/tts_debug.log
    exit 1
fi

# Save text to temp file
TEMP_FILE=$(mktemp /tmp/tts_cursor_XXXXXX.txt)
echo "$TEXT" > "$TEMP_FILE"

notify "Speaking from cursor (${#TEXT} chars)"

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
                    notify-send "TTS Speaking" "${CURRENT:0:100}$([ ${#CURRENT} -gt 100 ] && echo '...')" -t 5000 -r 12345 2>/dev/null
                fi
            fi
            sleep 0.2
        done

        notify-send "TTS" "Finished speaking" -t 1500 -r 12345 2>/dev/null
    ) & disown
fi
