#!/bin/bash
# Sway & Hyprland Keyboard Shortcuts Setup
# Adds bindsym entries to config files

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TTS_ROOT="$(dirname "$SCRIPT_DIR")"

CMD_CURSOR="$TTS_ROOT/speak_from_cursor.sh"
CMD_DOC="$TTS_ROOT/speak_active_doc.sh"
CMD_SELECTION="$TTS_ROOT/speak_selection.sh"
CMD_STOP="$TTS_ROOT/stop_speaking.sh"

echo "Setting up Sway/Hyprland keyboard shortcuts..."

# Ensure scripts are executable
chmod +x "$CMD_CURSOR" "$CMD_DOC" "$CMD_SELECTION" "$CMD_STOP"

# Detect which compositor is in use
detect_compositor() {
    if [ -n "$SWAYSOCK" ]; then
        echo "sway"
    elif [ -n "$HYPRLAND_INSTANCE_SIGNATURE" ]; then
        echo "hyprland"
    else
        # Check config files
        if [ -f "$HOME/.config/sway/config" ]; then
            echo "sway"
        elif [ -f "$HOME/.config/hypr/hyprland.conf" ]; then
            echo "hyprland"
        else
            echo "unknown"
        fi
    fi
}

COMPOSITOR=$(detect_compositor)
echo "  Detected compositor: $COMPOSITOR"

# Sway configuration
setup_sway() {
    local config_file="$HOME/.config/sway/config"
    local config_dir
    config_dir=$(dirname "$config_file")

    mkdir -p "$config_dir"

    # Check if our shortcuts already exist
    if grep -q "TTS: Speak Selected" "$config_file" 2>/dev/null; then
        echo "  Sway shortcuts already configured"
        return
    fi

    # Append shortcuts
    cat >> "$config_file" << EOF

# TTS Keyboard Shortcuts
# Added by TTS setup script
# Shift+Alt+S: Read active document from beginning
bindsym Shift+Alt+s exec $CMD_DOC
# Shift+Alt+C: Speak selected text (clipboard)
bindsym Shift+Alt+c exec $CMD_SELECTION
# Shift+Alt+Q: Stop speaking
bindsym Shift+Alt+q exec $CMD_STOP
EOF

    echo "  Added shortcuts to $config_file"
    echo "  Run 'sway reload' to apply changes"
}

# Hyprland configuration
setup_hyprland() {
    local config_file="$HOME/.config/hypr/hyprland.conf"
    local config_dir
    config_dir=$(dirname "$config_file")

    mkdir -p "$config_dir"

    # Check if our shortcuts already exist
    if grep -q "TTS: Speak Selected" "$config_file" 2>/dev/null; then
        echo "  Hyprland shortcuts already configured"
        return
    fi

    # Append shortcuts
    cat >> "$config_file" << EOF

# TTS Keyboard Shortcuts
# Added by TTS setup script
# Shift+Alt+S: Read active document from beginning
bind = SHIFT ALT, s, exec, $CMD_DOC
# Shift+Alt+C: Speak selected text (clipboard)
bind = SHIFT ALT, c, exec, $CMD_SELECTION
# Shift+Alt+Q: Stop speaking
bind = SHIFT ALT, q, exec, $CMD_STOP
EOF

    echo "  Added shortcuts to $config_file"
    echo "  Run 'hyprctl reload' to apply changes"
}

case "$COMPOSITOR" in
    sway)
        setup_sway
        ;;
    hyprland)
        setup_hyprland
        ;;
    *)
        echo "  Unknown compositor. Manual setup required."
        echo "  Add these lines to your config:"
        echo ""
        echo "  For Sway:"
        echo "    bindsym Shift+Alt+s exec $CMD_DOC"
        echo "    bindsym Shift+Alt+c exec $CMD_SELECTION"
        echo "    bindsym Shift+Alt+q exec $CMD_STOP"
        echo ""
        echo "  For Hyprland:"
        echo "    bind = SHIFT ALT, s, exec, $CMD_DOC"
        echo "    bind = SHIFT ALT, c, exec, $CMD_SELECTION"
        echo "    bind = SHIFT ALT, q, exec, $CMD_STOP"
        ;;
esac

echo "Sway/Hyprland shortcuts configured!"
