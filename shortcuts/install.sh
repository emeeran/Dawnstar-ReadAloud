#!/bin/bash
# TTS Keyboard Shortcuts Auto-Installer
# Detects desktop environment and runs appropriate setup script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Detect desktop environment
detect_de() {
    local de="unknown"

    # Check XDG_CURRENT_DESKTOP first
    if [ -n "$XDG_CURRENT_DESKTOP" ]; then
        de=$(echo "$XDG_CURRENT_DESKTOP" | tr '[:upper:]' '[:lower:]')

        # Handle compound names (e.g., "ubuntu:gnome")
        if echo "$de" | grep -q ":"; then
            de=$(echo "$de" | cut -d: -f2)
        fi
    fi

    # Fallback to process detection
    if [ "$de" = "unknown" ] || [ "$de" = "" ]; then
        if pgrep -x "gnome-shell" > /dev/null; then
            de="gnome"
        elif pgrep -x "plasmashell" > /dev/null; then
            de="kde"
        elif pgrep -x "xfce4-session" > /dev/null; then
            de="xfce"
        elif pgrep -x "sway" > /dev/null; then
            de="sway"
        elif pgrep -x "hyprland" > /dev/null; then
            de="hyprland"
        elif [ -n "$SWAYSOCK" ]; then
            de="sway"
        elif [ -n "$HYPRLAND_INSTANCE_SIGNATURE" ]; then
            de="hyprland"
        fi
    fi

    # Normalize
    case "$de" in
        *gnome*|*ubuntu*|*pop*)
            echo "gnome"
            ;;
        *kde*|*plasma*)
            echo "kde"
            ;;
        *xfce*)
            echo "xfce"
            ;;
        *sway*)
            echo "sway"
            ;;
        *hyprland*)
            echo "hyprland"
            ;;
        *)
            echo "$de"
            ;;
    esac
}

DE=$(detect_de)

echo "========================================="
echo "TTS Keyboard Shortcuts Installer"
echo "========================================="
echo ""
echo "Detected desktop environment: $DE"
echo ""

# Run appropriate setup script
case "$DE" in
    gnome)
        echo "Running GNOME setup..."
        bash "$SCRIPT_DIR/gnome.sh"
        ;;
    kde)
        echo "Running KDE setup..."
        bash "$SCRIPT_DIR/kde.sh"
        ;;
    xfce)
        echo "Running XFCE setup..."
        bash "$SCRIPT_DIR/xfce.sh"
        ;;
    sway|hyprland)
        echo "Running Sway/Hyprland setup..."
        bash "$SCRIPT_DIR/sway.sh"
        ;;
    *)
        echo "Unsupported desktop environment: $DE"
        echo ""
        echo "Please manually add these keyboard shortcuts:"
        echo ""
        echo "  Shift+Alt+S: $SCRIPT_DIR/../speak_active_doc.sh"
        echo "  Shift+Alt+C: $SCRIPT_DIR/../speak_selection.sh"
        echo "  Shift+Alt+Q: $SCRIPT_DIR/../stop_speaking.sh"
        echo ""
        echo "Or run one of the specific scripts:"
        echo "  $SCRIPT_DIR/gnome.sh"
        echo "  $SCRIPT_DIR/kde.sh"
        echo "  $SCRIPT_DIR/xfce.sh"
        echo "  $SCRIPT_DIR/sway.sh"
        exit 1
        ;;
esac

echo ""
echo "========================================="
echo "Setup complete!"
echo "========================================="
echo ""
echo "Keyboard shortcuts:"
echo "  Shift+Alt+S - Read active document"
echo "  Shift+Alt+C - Speak selection (clipboard)"
echo "  Shift+Alt+Q - Stop speaking"
echo ""
echo "You may need to log out and back in for shortcuts to take effect."
