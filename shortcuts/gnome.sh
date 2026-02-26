#!/bin/bash
# GNOME Keyboard Shortcuts Setup
# Uses gsettings for GNOME/GTK-based desktops

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TTS_ROOT="$(dirname "$SCRIPT_DIR")"

CMD_SPEAK="$TTS_ROOT/speak_from_cursor.sh"
CMD_PAUSE="$TTS_ROOT/pause_speaking.sh"
CMD_STOP="$TTS_ROOT/stop_speaking.sh"

SCHEMA_KEYS="org.gnome.settings-daemon.plugins.media-keys"
SCHEMA_BINDING="${SCHEMA_KEYS}.custom-keybinding"

echo "Setting up GNOME keyboard shortcuts..."

# Ensure scripts are executable
chmod +x "$CMD_SPEAK" "$CMD_PAUSE" "$CMD_STOP"

# Define shortcuts (index, name, command, binding)
# Custom0 is reserved (e.g., for Flameshot)
# Keybindings: Shift+Meta (Super) = <Shift><Super>
SHORTCUTS=(
    "1|Speak Selection|/bin/bash -lc '$CMD_SPEAK'|<Shift><Super>s"
    "2|Pause Speaking|/bin/bash -lc '$CMD_PAUSE'|<Shift><Super>c"
    "3|Stop Speaking|/bin/bash -lc '$CMD_STOP'|<Shift><Super>q"
)

# Build binding list
BINDING_LIST="["
FIRST=true
for entry in "${SHORTCUTS[@]}"; do
    IFS='|' read -r idx name cmd binding <<< "$entry"
    if [ "$FIRST" = true ]; then
        FIRST=false
    else
        BINDING_LIST+=", "
    fi
    BINDING_LIST+="\"/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom${idx}/\""
done
BINDING_LIST+="]"

# Preserve custom0 (often used by other apps like Flameshot)
gsettings set "$SCHEMA_KEYS" custom-keybindings "$BINDING_LIST"

# Set up each shortcut
for entry in "${SHORTCUTS[@]}"; do
    IFS='|' read -r idx name cmd binding <<< "$entry"

    PATH_KEY="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom${idx}/"

    gsettings set "${SCHEMA_BINDING}:${PATH_KEY}" name "$name"
    gsettings set "${SCHEMA_BINDING}:${PATH_KEY}" command "$cmd"
    gsettings set "${SCHEMA_BINDING}:${PATH_KEY}" binding "$binding"

    echo "  Set '$name' to $binding"
done

echo "GNOME shortcuts configured!"
