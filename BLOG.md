# Building a Neural TTS Tool for Linux with Global Hotkeys

If you read a lot on screen—documentation, articles, ebooks—you know the eye strain. Existing TTS options are either robotic, paid, or require copying text into a browser. I wanted something faster: highlight text anywhere, hit a hotkey, hear natural speech. Here's how I built it.

## The Goal

A simple TTS system that:
- Uses neural voices (not robotic synthesis)
- Works with global keyboard shortcuts in any app
- Caches audio for instant replay of repeated phrases
- Handles files, PDFs, EPUBs, and URLs
- Works on both X11 and Wayland

## The Solution

A Python CLI that leverages Microsoft Edge TTS (Azure neural voices, free) with MD5-based caching and desktop integration.

### How It Works

1. **Text Input**: Accepts direct text, files, URLs, or clipboard via `xclip` (X11) or `wl-paste` (Wayland)
2. **Chunking**: Splits text at sentence boundaries (`. ! ?`) for natural speech rhythm
3. **TTS Engine**: Primary Edge TTS, with gTTS and eSpeak as fallbacks
4. **Caching**: Stores audio in `~/.cache/tts_app/` keyed by `md5(text + lang + speed)`
5. **Playback**: Auto-detects player (mpg123 → paplay → cvlc → ffplay)

## The Setup

```bash
#!/bin/bash
# Install Dawnstar ReadAloud

# System dependencies
sudo apt install mpg123 xclip poppler-utils

# Clone and install
git clone https://github.com/emeeran/Dawnstar-ReadAloud.git tts && cd tts
python3 -m venv .venv
./.venv/bin/pip install -e .

# Test it
./tts "Hello! This sounds surprisingly natural."

# Set up global hotkeys
python3 configure.py
```

## Setting Up Keyboard Shortcuts

The `configure.py` script auto-detects your desktop and registers hotkeys. For GNOME via `gsettings`:

```bash
# Speak selection: Ctrl+Alt+S
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ name 'TTS Speak'
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ command '/home/you/.local/bin/tts-speak'
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/ binding '<Ctrl><Alt>s'

# Stop speaking: Ctrl+Alt+Q
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom1/ name 'TTS Stop'
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom1/ command '/home/you/.local/bin/tts-stop'
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom1/ binding '<Ctrl><Alt>q'

# Register them
gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "['/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/', '/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom1/']"
```

On X11, the primary selection (highlighted text) is prioritized over clipboard—you don't need to copy, just highlight.

## The Result

Highlight any text, press `Ctrl+Alt+S`, and hear it spoken:

```bash
# Cache stats after using the hotkey
./tts --cache-stats

Cache Statistics:
  Files: 12
  Size: 4.2 MB / 500 MB
  Location: /home/you/.cache/tts_app/
```

First playback takes ~1 second (network request), subsequent plays of the same text are instant.

## Usage Examples

```bash
./tts "Direct text"              # Speak directly
./tts document.txt               # Read a file
./tts book.epub                  # Read EPUB (skips front matter)
./tts https://example.com        # Read a webpage
cat notes.txt | ./tts -          # Read from stdin
./tts -l en-uk -s slow file.txt  # British English, slow speed
```

## Requirements

- **Python 3.12+**
- **mpg123** (recommended audio player)
- **xclip** or **wl-clipboard** (for keyboard shortcuts)
- **poppler-utils** (PDF support, optional)

```bash
# Ubuntu/Debian
sudo apt install mpg123 xclip poppler-utils
```

## Why This Matters

The best TTS system is the one you actually use. By reducing friction to a single hotkey, I find myself listening more—documentation while cooking, proofreading by ear, articles during walks. The neural voices make it pleasant rather than tolerable.

The modular architecture makes it easy to extend: add languages in `core/constants.py`, swap backends in `core/engine.py`. Full documentation at [USER_MANUAL.md](USER_MANUAL.md).

Happy listening!
