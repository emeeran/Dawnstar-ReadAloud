#!/bin/bash
# Sway & Hyprland Keyboard Shortcuts Setup
# Adds bindsym entries to config files

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TTS_ROOT="$(dirname "$SCRIPT_DIR")"

CMD_SPEAK="$TTS_ROOT/speak_from_cursor.sh"
CMD_SELECTION="$TTS_ROOT/speak_selection.sh"
CMD_STOP="$TTS_ROOT/stop_speaking.sh"

echo "Setting up Sway/Hyprland keyboard shortcuts..."

# Ensure scripts are executable
chmod +x "$CMD_SPEAK" "$CMD_SELECTION" "$CMD_STOP"

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
    if grep -q "TTS: Speak Selection" "$config_file" 2>/dev/null; then
        echo "  Sway shortcuts already configured"
        return
    fi

    # Append shortcuts
    # Mod4 is the Super/Meta key
    cat >> "$config_file" << 'EOF'

# TTS Keyboard Shortcuts
# Added by TTS setup script
bindsym Ctrl+Alt+s exec CMD_SPEAK_PLACEHOLDER
bindsym Ctrl+Alt+c exec CMD_SELECTION_PLACEHOLDER
bindsym Ctrl+Alt+q exec CMD_STOP_PLACEHOLDER
EOF

    # Replace placeholders with actual paths
    sed -i "s|CMD_SPEAK_PLACEHOLDER|$CMD_SPEAK|g" "$config_file"
    sed -i "s|CMD_SELECTION_PLACEHOLDER|$CMD_SELECTION|g" "$config_file"
    sed -i "s|CMD_STOP_PLACEHOLDER|$CMD_STOP|g" "$config_file"

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
    if grep -q "TTS: Speak Selection" "$config_file" 2>/dev/null; then
        echo "  Hyprland shortcuts already configured"
        return
    fi

    # Append shortcuts
    # SUPER is the Meta/Super key in Hyprland
    cat >> "$config_file" << 'EOF'

# TTS Keyboard Shortcuts
# Added by TTS setup script
bind = CTRL ALT, s, exec, CMD_SPEAK_PLACEHOLDER
bind = CTRL ALT, c, exec, CMD_SELECTION_PLACEHOLDER
bind = CTRL ALT, q, exec, CMD_STOP_PLACEHOLDER
EOF

    # Replace placeholders with actual paths
    sed -i "s|CMD_SPEAK_PLACEHOLDER|$CMD_SPEAK|g" "$config_file"
    sed -i "s|CMD_SELECTION_PLACEHOLDER|$CMD_SELECTION|g" "$config_file"
    sed -i "s|CMD_STOP_PLACEHOLDER|$CMD_STOP|g" "$config_file"

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
        echo "    bindsym Ctrl+Alt+s exec $CMD_SPEAK"
        echo "    bindsym Ctrl+Alt+c exec $CMD_SELECTION"
        echo "    bindsym Ctrl+Alt+q exec $CMD_STOP"
        echo ""
        echo "  For Hyprland:"
        echo "    bind = CTRL ALT, s, exec, $CMD_SPEAK"
        echo "    bind = CTRL ALT, c, exec, $CMD_SELECTION"
        echo "    bind = CTRL ALT, q, exec, $CMD_STOP"
        ;;
esac

echo "Sway/Hyprland shortcuts configured!"
