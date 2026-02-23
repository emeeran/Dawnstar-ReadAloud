# 🗣️ Enhanced TTS Application

A robust, production-ready Text-to-Speech application for Linux. Read text files, PDFs, URLs, or highlighting text on your screen.

## ✨ Highlights
- **🚀 Instant Playback**: Smart caching system for zero-latency repeats.
- **🖥️ System Integration**: Speak selected text globally with `Ctrl+Alt+S`.
- **🌍 Multi-Language**: Support for US English, UK English, and Tamil.
- **🛡️ Robust**: Auto-detection of audio players (mpg123, VLC) and error recovery.

## 📚 Documentation

Detailed documentation is broken down into:

- **[DOCUMENTATION.md](DOCUMENTATION.md)**: Installation, Troubleshooting, and Advanced usage.
- **[FEATURES_AND_COMMANDS.md](FEATURES_AND_COMMANDS.md)**: Full CLI reference and feature list.

## 🚀 Quick Start

1. **Install Dependencies**:
   ```bash
   sudo apt install mpg123 xclip
   ./venv/bin/pip install -r requirements.txt
   ```

2. **Run the App**:
   ```bash
   ./tts document.txt
   ```

3. **Install Keyboard Shortcut**:
   ```bash
   python3 setup_shortcut.py
   ```
   Now press **Ctrl+Alt+S** to read any highlighted text!

4. **Interactive Mode**:
   ```bash
   ./tts
   ```
   Launches a menu to change language, speed, and enter text.

## 📦 Project Structure

```text
tts/
├── app.py                      # Main Application
├── tts                         # Launcher Script
├── setup_shortcut.py           # Shortcut Installer
├── speak_selection.sh          # Selection Handler
├── DOCUMENTATION.md            # Master Guide
├── FEATURES_AND_COMMANDS.md    # Reference Guide
└── README.md                   # This file
```
