# Enhanced TTS Application

A lightweight, neural-network-based Text-to-Speech application for Linux with global keyboard shortcuts, smart caching, and multi-language support.

## Features

- **Neural Voices** - High-quality Microsoft Azure neural voices via Edge TTS
- **Smart Caching** - Instant replay of previously spoken text
- **System Integration** - Global keyboard shortcuts work in any application
- **Multiple Input Sources** - Files, PDFs, URLs, clipboard, stdin
- **Cross-Platform Clipboard** - Works on both X11 and Wayland
- **Multi-Language** - US English, UK English, and Tamil

## Quick Start

```bash
# Install dependencies
sudo apt install mpg123 xclip
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt

# Run the application
./tts "Hello, world!"

# Set up keyboard shortcuts
python3 configure.py
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Alt+S` | Speak selected/copied text |
| `Ctrl+Alt+Q` | Stop speaking |

## Basic Usage

```bash
./tts "text to speak"           # Direct text
./tts document.txt              # Read file
./tts -l en-uk -s slow file.txt # British English, slow speed
cat notes.txt | ./tts -         # Read from stdin
```

## Documentation

- **[USER_MANUAL.md](USER_MANUAL.md)** - Complete user manual with detailed usage, troubleshooting, and configuration
- **[CLAUDE.md](CLAUDE.md)** - Developer documentation and architecture

## Requirements

- Python 3.12+
- mpg123 (audio playback)
- xclip or wl-clipboard (keyboard shortcuts)

## License

MIT License
