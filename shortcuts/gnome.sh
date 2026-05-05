#!/bin/bash
# GNOME Keyboard Shortcuts Setup (Ultra-Safe/Additive)
# Merges shortcuts without ever deleting existing ones.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TTS_ROOT="$(dirname "$SCRIPT_DIR")"

CMD_SPEAK="/bin/bash -lc '$TTS_ROOT/speak_from_cursor.sh'"
CMD_SELECTION="/bin/bash -lc '$TTS_ROOT/speak_selection.sh'"
CMD_STOP="/bin/bash -lc '$TTS_ROOT/stop_speaking.sh'"

SCHEMA_KEYS="org.gnome.settings-daemon.plugins.media-keys"
SCHEMA_BINDING="${SCHEMA_KEYS}.custom-keybinding"

echo "Setting up GNOME keyboard shortcuts..."

# 1. Get current paths
CURRENT_PATHS=$(gsettings get "$SCHEMA_KEYS" custom-keybindings | grep -o "'/[^']*'" | sed "s/'//g")

declare -A ALL_PATHS
MAX_IDX=-1
for p in $CURRENT_PATHS; do
    [[ "$p" != */ ]] && p="${p}/"
    ALL_PATHS["$p"]=1
    IDX=$(echo "$p" | grep -o 'custom[0-9]*' | sed 's/custom//')
    if [[ -n "$IDX" ]]; then
        if (( IDX > MAX_IDX )); then MAX_IDX=$IDX; fi
    fi
done

# 2. Our target shortcuts
declare -A TARGETS
TARGETS["Speak From Cursor"]="$CMD_SPEAK|<Control><Alt>s"
TARGETS["Speak Selected"]="$CMD_SELECTION|<Control><Alt>c"
TARGETS["Stop Speaking"]="$CMD_STOP|<Control><Alt>q"

# 3. Update or Add
for NAME in "${!TARGETS[@]}"; do
    IFS='|' read -r CMD BINDING <<< "${TARGETS[$NAME]}"
    FOUND_PATH=""
    
    # Search in existing
    for p in "${!ALL_PATHS[@]}"; do
        EXISTING_NAME=$(gsettings get "${SCHEMA_BINDING}:${p}" name | sed "s/^'//;s/'$//")
        EXISTING_CMD=$(gsettings get "${SCHEMA_BINDING}:${p}" command | sed "s/^'//;s/'$//")
        if [[ "$EXISTING_NAME" == "$NAME" || "$EXISTING_CMD" == "$CMD" ]]; then
            FOUND_PATH="$p"
            break
        fi
    done
    
    if [[ -n "$FOUND_PATH" ]]; then
        echo "  Updating '$NAME' at $FOUND_PATH"
    else
        MAX_IDX=$((MAX_IDX + 1))
        FOUND_PATH="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom${MAX_IDX}/"
        ALL_PATHS["$FOUND_PATH"]=1
        echo "  Creating '$NAME' at $FOUND_PATH"
    fi
    
    gsettings set "${SCHEMA_BINDING}:${FOUND_PATH}" name "$NAME"
    gsettings set "${SCHEMA_BINDING}:${FOUND_PATH}" command "$CMD"
    gsettings set "${SCHEMA_BINDING}:${FOUND_PATH}" binding "$BINDING"
done

# 4. Write back (Sorted)
FINAL_LIST="["
FIRST=true
for p in $(echo "${!ALL_PATHS[@]}" | tr ' ' '\n' | sort -V); do
    if [ "$FIRST" = true ]; then FIRST=false; else FINAL_LIST+=", "; fi
    FINAL_LIST+="'$p'"
done
FINAL_LIST+="]"

gsettings set "$SCHEMA_KEYS" custom-keybindings "$FINAL_LIST"
echo "GNOME shortcuts configured successfully!"
