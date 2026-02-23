#!/bin/bash
# XFCE Keyboard Shortcuts Setup
# Uses xfconf-query for XFCE4

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TTS_ROOT="$(dirname "$SCRIPT_DIR")"

CMD_SPEAK="$TTS_ROOT/speak_selection.sh"
CMD_STOP="$TTS_ROOT/stop_speaking.sh"

echo "Setting up XFCE keyboard shortcuts..."

# Ensure scripts are executable
chmod +x "$CMD_SPEAK" "$CMD_STOP"

# Check if xfconf-query is available
if ! command -v xfconf-query &> /dev/null; then
    echo "Error: xfconf-query not found. Is XFCE installed?"
    exit 1
fi

# XFCE stores keyboard shortcuts in xfce4-keyboard-shortcuts channel
# We need to find the next available custom shortcut slot

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
    # Extract number from last custom (e.g., /commands/custom/12 -> 12)
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

    # Set the shortcut (XFCE format: <Primary><Alt>s)
    # Convert Ctrl to <Primary> format
    local xfce_shortcut="${shortcut//Ctrl/<Primary>}"
    xfce_shortcut="${xfce_shortcut//Alt/<Alt>}"

    xfconf-query -c "$CHANNEL" -p "/commands/custom/$slot" -t string -s "$cmd" --create

    echo "  Added '$name' at slot $slot"
}

# Add Speak Selection shortcut
SPEAK_SLOT=$NEXT_SLOT
add_shortcut "$SPEAK_SLOT" "Speak Selection" "$CMD_SPEAK" "Ctrl+Alt+s"

# Add Stop Speaking shortcut
STOP_SLOT=$((NEXT_SLOT + 1))
add_shortcut "$STOP_SLOT" "Stop Speaking" "$CMD_STOP" "Ctrl+Alt+q"

# Note: In XFCE, you may also need to set the actual key binding
# This is typically done through the keyboard settings GUI
# The commands above set up the command, but key binding may need manual setup

echo ""
echo "XFCE shortcuts configured!"
echo ""
echo "Note: You may need to manually bind the keys in:"
echo "  Settings > Keyboard > Application Shortcuts"
echo ""
echo "Or run these commands:"
echo "  xfconf-query -c xfce4-keyboard-shortcuts -p '/commands/custom/$SPEAK_SLOT' -t string -s '$CMD_SPEAK'"
echo "  xfconf-query -c xfce4-keyboard-shortcuts -p '/commands/custom/$STOP_SLOT' -t string -s '$CMD_STOP'"
