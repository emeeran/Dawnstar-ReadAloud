#!/bin/bash
# XFCE Keyboard Shortcuts Setup
# Uses xfconf-query for XFCE4

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TTS_ROOT="$(dirname "$SCRIPT_DIR")"

CMD_CURSOR="$TTS_ROOT/speak_from_cursor.sh"
CMD_DOC="$TTS_ROOT/speak_active_doc.sh"
CMD_SELECTION="$TTS_ROOT/speak_selection.sh"
CMD_STOP="$TTS_ROOT/stop_speaking.sh"

echo "Setting up XFCE keyboard shortcuts..."

# Ensure scripts are executable
chmod +x "$CMD_CURSOR" "$CMD_DOC" "$CMD_SELECTION" "$CMD_STOP"

# Check if xfconf-query is available
if ! command -v xfconf-query &> /dev/null; then
    echo "Error: xfconf-query not found. Is XFCE installed?"
    exit 1
fi

CHANNEL="xfce4-keyboard-shortcuts"

# Get existing custom shortcuts
get_existing_shortcuts() {
    xfconf-query -c "$CHANNEL" -l | grep "/custom" | sort -V | tail -1
}

# Find next available slot
LAST_CUSTOM=$(get_existing_shortcuts)
if [ -z "$LAST_CUSTOM" ]; then
    NEXT_SLOT=0
else
    NEXT_SLOT=$(echo "$LAST_CUSTOM" | grep -o '[0-9]*$')
    NEXT_SLOT=$((NEXT_SLOT + 1))
fi

echo "  Using custom shortcut slots starting at $NEXT_SLOT"

# Add a custom keyboard shortcut
add_shortcut() {
    local slot=$1
    local name=$2
    local cmd=$3
    local shortcut=$4

    # Set the command
    xfconf-query -c "$CHANNEL" -p "/commands/custom/$slot" -t string -s "$cmd" --create

    echo "  Added '$name' at slot $slot ($shortcut)"
}

# Add all 4 shortcuts
add_shortcut "$NEXT_SLOT" "Speak From Cursor" "$CMD_CURSOR" "Shift+Alt+f"
add_shortcut "$((NEXT_SLOT + 1))" "Read Active Document" "$CMD_DOC" "Shift+Alt+d"
add_shortcut "$((NEXT_SLOT + 2))" "Speak Selected" "$CMD_SELECTION" "Shift+Alt+c"
add_shortcut "$((NEXT_SLOT + 3))" "Stop Speaking" "$CMD_STOP" "Shift+Alt+q"

echo ""
echo "XFCE shortcuts configured!"
echo ""
echo "Note: You may need to manually bind the keys in:"
echo "  Settings > Keyboard > Application Shortcuts"
