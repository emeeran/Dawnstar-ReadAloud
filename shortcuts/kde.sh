#!/bin/bash
# KDE Plasma Keyboard Shortcuts Setup
# Uses kwriteconfig5 for KDE kglobalaccel

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TTS_ROOT="$(dirname "$SCRIPT_DIR")"

CMD_CURSOR="$TTS_ROOT/speak_from_cursor.sh"
CMD_DOC="$TTS_ROOT/speak_active_doc.sh"
CMD_SELECTION="$TTS_ROOT/speak_selection.sh"
CMD_STOP="$TTS_ROOT/stop_speaking.sh"

echo "Setting up KDE Plasma keyboard shortcuts..."

# Ensure scripts are executable
chmod +x "$CMD_CURSOR" "$CMD_DOC" "$CMD_SELECTION" "$CMD_STOP"

# Speak From Cursor shortcut
kwriteconfig5 --file kglobalshortcutsrc --group kwin --key "TTS Speak From Cursor" \
    "TTS Speak From Cursor,,($CMD_CURSOR),Shift+Alt+F,Shift+Alt+F,TTS Speak From Cursor"

# Read Active Document shortcut
kwriteconfig5 --file kglobalshortcutsrc --group kwin --key "TTS Read Active Document" \
    "TTS Read Active Document,,($CMD_DOC),Shift+Alt+D,Shift+Alt+D,TTS Read Active Document"

# Speak Selected shortcut
kwriteconfig5 --file kglobalshortcutsrc --group kwin --key "TTS Speak Selected" \
    "TTS Speak Selected,,($CMD_SELECTION),Shift+Alt+C,Shift+Alt+C,TTS Speak Selected"

# Stop Speaking shortcut
kwriteconfig5 --file kglobalshortcutsrc --group kwin --key "TTS Stop Speaking" \
    "TTS Stop Speaking,,($CMD_STOP),Shift+Alt+Q,Shift+Alt+Q,TTS Stop Speaking"

echo "  Configured 'Speak From Cursor' to Shift+Alt+F"
echo "  Configured 'Read Active Document' to Shift+Alt+D"
echo "  Configured 'Speak Selected' to Shift+Alt+C"
echo "  Configured 'Stop Speaking' to Shift+Alt+Q"
echo ""
echo "Note: You may need to:"
echo "  1. Log out and back in, or"
echo "  2. Run: kbuildsycoca5 && kglobalaccel5 --replace &"
echo "  3. Check System Settings > Shortcuts"

echo "KDE shortcuts configured!"
