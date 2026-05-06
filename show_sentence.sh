#!/bin/bash
# Display current sentence in a persistent, non-intrusive overlay
# Uses zenity for a clean floating window

SENTENCE_FILE="${1:-/tmp/tts_cursor_state/current_sentence.txt}"
WINDOW_TITLE="TTS Speaking"

# Create/update a zenity text-info window
# --no-wrap: don't wrap text (we control line breaks)
# --width/--height: compact size
# --sticky: stay on top
# --no-buttons: no close button (we handle cleanup)

# Kill any existing instance
pkill -f "zenity.*TTS Speaking" 2>/dev/null || true

# Show the sentence in a floating window
zenity --text-info \
    --title="$WINDOW_TITLE" \
    --width=600 \
    --height=100 \
    --sticky \
    --no-buttons \
    --modal=false \
    2>/dev/null &

ZENITY_PID=$!

# Monitor sentence file and update zenity
LAST_SENTENCE=""
while true; do
    if [ -f "$SENTENCE_FILE" ]; then
        CURRENT=$(cat "$SENTENCE_FILE" 2>/dev/null)
        if [ -n "$CURRENT" ] && [ "$CURRENT" != "$LAST_SENTENCE" ]; then
            LAST_SENTENCE="$CURRENT"
            # Send to zenity via stdin (if still running)
            if kill -0 $ZENITY_PID 2>/dev/null; then
                echo "$CURRENT" 
            else
                break
            fi
        fi
    elif [ -z "$CURRENT" ] && ! pgrep -f "tts.*sentence" > /dev/null 2>&1; then
        # TTS finished and no more content
        break
    fi
    sleep 0.1
done

# Cleanup
kill $ZENITY_PID 2>/dev/null || true
