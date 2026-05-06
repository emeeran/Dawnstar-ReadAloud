#!/bin/bash
# Read the active window's document from the beginning.
#
# Detects the focused application's source (URL or file path) and
# passes it to `tts` for full content extraction:
#   - URLs: skip ads/nav, extract main article
#   - PDF/EPUB: skip front matter, start from chapter 1
#   - Text files: read from beginning
#
# Shortcut: Shift+Alt+S

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TTS_APP="$SCRIPT_DIR/tts"
SOURCE_SCRIPT="$SCRIPT_DIR/get_active_source.py"
OVERLAY_SCRIPT="$SCRIPT_DIR/sentence_overlay.py"
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

echo "$(date) - speak_active_doc: starting" >> /tmp/tts_debug.log

# ── Detect active window's source (URL or file path) ──
if [ -f "$SOURCE_SCRIPT" ]; then
    SOURCE=$(python3 "$SOURCE_SCRIPT" 2>>/tmp/tts_debug.log)
    echo "$(date) - get_active_source.py result: '${SOURCE:-<empty>}'" >> /tmp/tts_debug.log
    if [ -n "$SOURCE" ]; then
        echo "$(date) - Detected source: $SOURCE" >> /tmp/tts_debug.log
        notify "Reading: ${SOURCE##*/}"

        # Start sentence overlay (visual highlighting)
        if [ -f "$OVERLAY_SCRIPT" ]; then
            python3 "$OVERLAY_SCRIPT" "$SENTENCE_FILE" &
            OVERLAY_PID=$!
            trap "kill $OVERLAY_PID 2>/dev/null" EXIT
        fi

        # Launch TTS with the source for full content extraction
        (
            "$TTS_APP" --sentence-file "$SENTENCE_FILE" "$SOURCE" > /dev/null 2>&1
            rm -f "$SENTENCE_FILE"
        ) & disown

        exit 0
    fi
fi

notify "No document detected. Open a file in a viewer or browser."
echo "$(date) - speak_active_doc: no source detected" >> /tmp/tts_debug.log
exit 1
