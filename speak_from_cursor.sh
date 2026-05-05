#!/bin/bash
# Speak from the active window's document source.
#
# Priority:
#   1. Detect active window source (URL from browser, file from viewer/editor)
#      → passes to `tts <source>` for full content extraction (chapter 1, skip ads)
#   2. Accessibility APIs (AT-SPI) → speak from cursor position
#   3. Clipboard fallback → speak selected text

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TTS_APP="$SCRIPT_DIR/tts"
ACCESSIBLE_SCRIPT="$SCRIPT_DIR/get_accessible_text.py"
SOURCE_SCRIPT="$SCRIPT_DIR/get_active_source.py"
STATE_DIR="/tmp/tts_cursor_state"
SENTENCE_FILE="$STATE_DIR/current_sentence.txt"

# Initialize state directory
mkdir -p "$STATE_DIR"
rm -f "$SENTENCE_FILE"

# Function to show notification
notify() {
    if command -v notify-send &> /dev/null; then
        notify-send "TTS" "$1" -t 2000 2>/dev/null
    fi
}

echo "$(date) - Starting speak_from_cursor.sh" >> /tmp/tts_debug.log

# ── Strategy 1: Detect active window's source (URL or file path) ──
# This passes the source to `tts` which handles:
#   - URLs: skip ads/nav, extract main article content
#   - PDF/EPUB: skip front matter, start from chapter 1
#   - Text files: read from beginning
if [ -x "$SOURCE_SCRIPT" ] || [ -f "$SOURCE_SCRIPT" ]; then
    SOURCE=$(python3 "$SOURCE_SCRIPT" 2>/dev/null)
    if [ -n "$SOURCE" ]; then
        echo "$(date) - Detected source: $SOURCE" >> /tmp/tts_debug.log
        notify "Reading: ${SOURCE##*/}"

        # Launch TTS with the source for full content extraction
        (
            "$TTS_APP" --sentence-file "$SENTENCE_FILE" "$SOURCE" > /dev/null 2>&1
            rm -f "$SENTENCE_FILE"
        ) & disown

        # Monitor sentence file for notifications
        if command -v notify-send &> /dev/null; then
            (
                LAST_SENTENCE=""
                while [ ! -f "$SENTENCE_FILE" ]; do
                    sleep 0.1
                    if ! pgrep -f "tts.*$SOURCE" > /dev/null 2>&1 && [ ! -f "$SENTENCE_FILE" ]; then
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

        exit 0
    fi
fi

# ── Strategy 2: Accessibility APIs (speak from cursor) ──
TEXT=""
METHOD=""

if [ -x "$ACCESSIBLE_SCRIPT" ] || [ -f "$ACCESSIBLE_SCRIPT" ]; then
    TEXT=$(python3 "$ACCESSIBLE_SCRIPT" 2>/dev/null)
    if [ -n "$TEXT" ]; then
        METHOD="accessibility"
    fi
fi

# ── Strategy 3: Primary selection (highlighted text, NOT clipboard) ──
# Clipboard is Ctrl+Alt+C's job. We only try primary selection (highlight).
if [ -z "$TEXT" ]; then
    echo "$(date) - Source detection failed, trying primary selection (highlight)" >> /tmp/tts_debug.log
    if command -v xclip &> /dev/null; then
        TEXT=$(xclip -o -selection primary 2>/dev/null)
        if [ -n "$TEXT" ]; then
            METHOD="primary-selection"
        fi
    fi
fi

echo "$(date) - Extracted text length: ${#TEXT} via $METHOD" >> /tmp/tts_debug.log

if [ -z "$TEXT" ]; then
    notify "No text found. Open a document or select text."
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
                    notify-send "TTS Speaking" "${CURRENT:0:100}$([ ${#CURRENT} -gt 100 ] && echo '...')" -t 5000 -r 12345 2>/dev/null
                fi
            fi
            sleep 0.2
        done

        notify-send "TTS" "Finished speaking" -t 1500 -r 12345 2>/dev/null
    ) & disown
fi
