#!/bin/bash
# Master Installer for Enhanced TTS (Docker Edition)
set -e

APP_NAME="tts"
BIN_DIR="$HOME/.local/bin"
IMAGE_NAME="enhanced-tts:latest"

echo "🚀 Installing Enhanced TTS..."

# 1. Build Docker Image
echo "📦 Building Docker Image..."
docker build -t "$IMAGE_NAME" .

# 2. Create Global TTS Wrapper
echo "→ Installing '$APP_NAME' command..."
mkdir -p "$BIN_DIR"

cat > "$BIN_DIR/$APP_NAME" <<EOF
#!/bin/bash
# Wrapper for Dockerized Enhanced TTS
# Detect User ID for PulseAudio checks
UID_VAL=\$(id -u)

# Determine PulseAudio Socket
if [ -z "\$XDG_RUNTIME_DIR" ]; then
    XDG_RUNTIME_DIR="/run/user/\$UID_VAL"
fi
PULSE_SOCK="\$XDG_RUNTIME_DIR/pulse/native"
PULSE_COOKIE="\$HOME/.config/pulse/cookie"

# Run with Home Mount, PulseAudio, and Label
docker run --rm -i \\
    --device /dev/snd \\
    -e PULSE_SERVER="unix:/run/user/\$UID_VAL/pulse/native" \\
    -e PULSE_COOKIE="/root/.config/pulse/cookie" \\
    -v "\$PULSE_SOCK:/run/user/\$UID_VAL/pulse/native" \\
    -v "\$PULSE_COOKIE:/root/.config/pulse/cookie" \\
    -v "\$HOME:\$HOME" \\
    -w "\$(pwd)" \\
    --label app=enhanced-tts \\
    $IMAGE_NAME "\$@"
EOF
chmod +x "$BIN_DIR/$APP_NAME"

# 3. Install Helper Scripts
echo "→ Installing Helper Scripts..."
cp speak_selection.sh "$BIN_DIR/tts-speak"
cp stop_speaking.sh "$BIN_DIR/tts-stop"
chmod +x "$BIN_DIR/tts-speak"
chmod +x "$BIN_DIR/tts-stop"

# 4. Run Configuration (Shortcuts & Desktop Entry)
echo "⚙️  Configuring System..."
python3 configure.py

echo ""
echo "✅ Installation Complete!"
echo "   CLI:      $APP_NAME \"Hello\""
echo "   Speak:    Ctrl+Alt+S"
echo "   Stop:     Ctrl+Alt+Q"
echo "   Menu:     Look for 'Enhanced TTS' in your app launcher."
