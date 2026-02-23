#!/bin/bash
# KDE Plasma Keyboard Shortcuts Setup
# Uses kwriteconfig5 for KDE kglobalaccel

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TTS_ROOT="$(dirname "$SCRIPT_DIR")"

CMD_SPEAK="$TTS_ROOT/speak_selection.sh"
CMD_STOP="$TTS_ROOT/stop_speaking.sh"

echo "Setting up KDE Plasma keyboard shortcuts..."

# Ensure scripts are executable
chmod +x "$CMD_SPEAK" "$CMD_STOP"

# KDE uses kglobalaccel5 config file
# The config is in ~/.config/kglobalaccel

CONFIG_FILE="$HOME/.config/kglobalaccel"

# Method 1: Use dbus to register shortcuts (works for running session)
register_shortcut() {
    local name="$1"
    local cmd="$2"
    local shortcut="$3"

    # Create a desktop file for the action
    local desktop_dir="$HOME/.local/share/applications"
    local desktop_file="$desktop_dir/tts-${name// /-}.desktop"

    mkdir -p "$desktop_dir"

    cat > "$desktop_file" << EOF
[Desktop Entry]
Type=Application
Name=TTS: $name
Exec=$cmd
Icon=audio-headset
StartupNotify=false
X-KDE-GlobalShortcutType=Action
EOF

    # Register via kwriteconfig5
    kwriteconfig5 --file "$CONFIG_FILE" --group "tts-${name// /-}" --key "Name" "$name"
    kwriteconfig5 --file "$CONFIG_FILE" --group "tts-${name// /-}" --key "Command" "$cmd"
    kwriteconfig5 --file "$CONFIG_FILE" --group "tts-${name// /-}" --key "Trigger" "$shortcut"

    echo "  Configured '$name' (requires restart or kglobalaccel5 reload)"
}

# Method 2: Simpler approach - use KDE's custom shortcuts config
# This creates entries in kglobalaccel that can be edited in System Settings

# Speak Selection shortcut
kwriteconfig5 --file kglobalshortcutsrc --group kwin --key "TTS Speak Selection" \
    "TTS Speak Selection,,($CMD_SPEAK),Ctrl+Alt+S,Ctrl+Alt+S,TTS Speak Selection"

# Stop Speaking shortcut
kwriteconfig5 --file kglobalshortcutsrc --group kwin --key "TTS Stop Speaking" \
    "TTS Stop Speaking,,($CMD_STOP),Ctrl+Alt+Q,Ctrl+Alt+Q,TTS Stop Speaking"

echo "  Configured 'Speak Selection' to Ctrl+Alt+S"
echo "  Configured 'Stop Speaking' to Ctrl+Alt+Q"
echo ""
echo "Note: You may need to:"
echo "  1. Log out and back in, or"
echo "  2. Run: kbuildsycoca5 && kglobalaccel5 --replace &"
echo "  3. Check System Settings > Shortcuts"

echo "KDE shortcuts configured!"
