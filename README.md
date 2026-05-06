# Dawnstar ReadAloud

A lightweight, neural-network-based Text-to-Speech application for Linux with global keyboard shortcuts, smart caching, and multi-language support.

## Features

- **Neural Voices** — High-quality Microsoft Azure neural voices via Edge TTS
- **Smart Caching** — Instant replay of previously spoken text with LRU eviction
- **Global Shortcuts** — Works in any application: cursor, document, selection, stop
- **Source Detection** — Automatically detects the active window's file or URL
- **Multiple Input Sources** — Files, PDFs, EPUBs, URLs, clipboard, stdin
- **Smart Content Extraction** — Skips ads/front matter, reads main content
- **Sentence Highlighting** — Visual notification shows current sentence being spoken
- **Multi-Language** — US English, UK English, and Tamil
- **Daemon Mode** — Low-latency background service for frequent use

## Quick Start

```bash
# Install system dependencies
sudo apt install mpg123 xclip poppler-utils

# Create virtual environment and install
python3 -m venv .venv
./.venv/bin/pip install -e .

# Speak text
./tts "Hello, world!"

# Set up global keyboard shortcuts
python3 configure.py
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Shift+Alt+S` | Read active document (PDF, EPUB, URL) |
| `Shift+Alt+C` | Speak selected/highlighted text |
| `Shift+Alt+Q` | Stop speaking |

## Basic Usage

```bash
./tts "text to speak"           # Direct text
./tts document.txt              # Read file
./tts book.epub                 # Read EPUB (skips front matter)
./tts report.pdf                # Read PDF (skips preface/TOC)
./tts https://example.com       # Read web article (skips ads)
./tts -l ta -s slow "வணக்கம்"   # Tamil at slow speed
cat notes.txt | ./tts -         # Read from stdin
```

## Documentation

- **[USER_MANUAL.md](USER_MANUAL.md)** — Complete user manual
- **[CLAUDE.md](CLAUDE.md)** — Developer documentation and architecture

## Requirements

- Python 3.12+
- mpg123 (audio playback)
- xclip or wl-clipboard (keyboard shortcuts)
- poppler-utils (PDF support, optional)

## License

MIT License — See [LICENSE](LICENSE) for details.
