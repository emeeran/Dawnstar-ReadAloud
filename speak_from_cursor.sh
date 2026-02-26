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

# Detect display server
is_wayland() {
    [ -n "$WAYLAND_DISPLAY" ] || [ -n "$HYPRLAND_INSTANCE_SIGNATURE" ]
}

# Function to get clipboard content
get_clipboard() {
    "$TTS_APP" --get-clipboard 2>/dev/null
}

# Try to get text via accessibility APIs (no scrolling!)
TEXT=""
METHOD=""

if [ -x "$ACCESSIBLE_SCRIPT" ]; then
    TEXT=$(python3 "$ACCESSIBLE_SCRIPT" 2>/dev/null)
    if [ -n "$TEXT" ]; then
        METHOD="accessibility"
    fi
fi

# Fallback to xdotool/wtype selection only if AT-SPI failed
if [ -z "$TEXT" ]; then
    # Save original clipboard to restore later
    ORIGINAL_CLIPBOARD=""
    if is_wayland; then
        ORIGINAL_CLIPBOARD=$(wl-paste --no-newline 2>/dev/null)
    else
        ORIGINAL_CLIPBOARD=$(xclip -selection clipboard -o 2>/dev/null)
    fi

    # Set a unique marker in clipboard to detect if copy succeeds
    MARKER="__TTS_MARKER_$$__"
    if is_wayland; then
        echo -n "$MARKER" | wl-copy 2>/dev/null
    else
        echo -n "$MARKER" | xclip -selection clipboard 2>/dev/null
    fi

    if is_wayland; then
        if command -v wtype &> /dev/null; then
            wtype -M shift -M control End
            sleep 0.15
            wtype -m shift -m control
            sleep 0.2
            wtype -M control c
            sleep 0.15
            wtype -m control
            sleep 0.4
            TEXT=$(get_clipboard)
            wtype Left
            METHOD="wayland-selection"
        elif command -v ydotool &> /dev/null; then
            ydotool key 42:1 29:1 107:1 107:0 29:0 42:0
            sleep 0.3
            ydotool key 29:1 46:1 46:0 29:0
            sleep 0.4
            TEXT=$(get_clipboard)
            ydotool key 105:1 105:0
            METHOD="ydotool-selection"
        fi
    else
        if command -v xdotool &> /dev/null; then
            WID=$(xdotool getactivewindow 2>/dev/null)
            if [ -n "$WID" ]; then
                xdotool key --window "$WID" --delay 100 Shift+Ctrl+End
                sleep 0.25
                xdotool key --window "$WID" --delay 100 Ctrl+c
                sleep 0.4
                TEXT=$(get_clipboard)
                xdotool key --window "$WID" --delay 50 Left
                METHOD="xdotool-selection"
            fi
        fi
    fi

    # Check if copy actually worked (clipboard changed from marker)
    if [ -z "$TEXT" ] || [ "$TEXT" = "$MARKER" ]; then
        # Copy failed - restore original clipboard and show error
        if [ -n "$ORIGINAL_CLIPBOARD" ]; then
            if is_wayland; then
                echo -n "$ORIGINAL_CLIPBOARD" | wl-copy 2>/dev/null
            else
                echo -n "$ORIGINAL_CLIPBOARD" | xclip -selection clipboard 2>/dev/null
            fi
        fi
        notify "Could not get text from cursor. Try selecting text first."
        exit 1
    fi

    # Restore original clipboard after successful copy
    if [ -n "$ORIGINAL_CLIPBOARD" ]; then
        ( sleep 1; if is_wayland; then echo -n "$ORIGINAL_CLIPBOARD" | wl-copy 2>/dev/null; else echo -n "$ORIGINAL_CLIPBOARD" | xclip -selection clipboard 2>/dev/null; fi ) & disown
    fi
fi

if [ -z "$TEXT" ]; then
    notify "No text found at cursor position."
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
