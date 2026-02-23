# TTS Application - Complete User Manual

A comprehensive guide to the Enhanced Text-to-Speech application for Linux.

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Installation](#2-installation)
3. [Quick Start](#3-quick-start)
4. [Basic Usage](#4-basic-usage)
5. [Command Reference](#5-command-reference)
6. [Keyboard Shortcuts](#6-keyboard-shortcuts)
7. [Languages and Voices](#7-languages-and-voices)
8. [Text Processing](#8-text-processing)
9. [Caching System](#9-caching-system)
10. [Advanced Usage](#10-advanced-usage)
11. [Daemon Mode](#11-daemon-mode)
12. [Troubleshooting](#12-troubleshooting)
13. [Configuration Files](#13-configuration-files)
14. [Uninstallation](#14-uninstallation)

---

## 1. Introduction

### Overview

The Enhanced TTS Application is a lightweight, neural-network-based text-to-speech system for Linux. It converts written text into natural-sounding speech using Microsoft Azure's neural voices via Edge TTS, with automatic fallback to Google TTS if needed.

### Key Features

| Feature | Description |
|---------|-------------|
| **Neural Voices** | High-quality AI-generated speech via Edge TTS |
| **Smart Caching** | Instant replay of previously spoken text |
| **Multi-Language** | US English, UK English, and Tamil support |
| **System Integration** | Global keyboard shortcuts for any application |
| **Multiple Input Sources** | Files, PDFs, URLs, clipboard, stdin |
| **Cross-Platform Clipboard** | Works on X11 and Wayland |
| **Adjustable Speed** | Slow, normal, or fast playback |

### System Requirements

- **Operating System**: Linux (Ubuntu/Debian recommended)
- **Python**: 3.12 or higher
- **Audio**: Working audio output (speakers/headphones)
- **Desktop**: GNOME, KDE, XFCE, Sway, or Hyprland (for keyboard shortcuts)

---

## 2. Installation

### Step 1: Install System Dependencies

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y mpg123 xclip

# Optional: For PDF support
sudo apt install -y poppler-utils

# Optional: For better web scraping
sudo apt install -y lynx
```

**Package Descriptions:**

| Package | Purpose | Required |
|---------|---------|----------|
| `mpg123` | MP3 audio playback | Yes |
| `xclip` | Clipboard access (X11) | Yes* |
| `wl-clipboard` | Clipboard access (Wayland) | Yes* |
| `poppler-utils` | PDF text extraction | No |
| `lynx` | Web content extraction | No |

*Either xclip (X11) or wl-clipboard (Wayland) is required for keyboard shortcuts.

### Step 2: Create Virtual Environment

```bash
cd /path/to/tts
python3 -m venv .venv
```

### Step 3: Install Python Dependencies

```bash
./.venv/bin/pip install -r requirements.txt
```

**Python Packages:**

| Package | Purpose |
|---------|---------|
| `edge-tts` | Microsoft Edge neural TTS engine |
| `gtts` | Google TTS (fallback engine) |
| `ebooklib` | EPUB ebook support |

### Step 4: Verify Installation

```bash
./tts --list-engines
```

Expected output:
```
Available TTS engines:
  ✓ edge
  ✓ gtts
  ✗ espeak
```

### Step 5: Configure System Integration (Optional)

```bash
python3 configure.py
```

This installs:
- Keyboard shortcuts (Ctrl+Alt+S, Ctrl+Alt+Q)
- Desktop entry for application menu
- Wrapper scripts in `~/.local/bin/`

---

## 3. Quick Start

### Your First Speech

```bash
./tts "Hello, world! Welcome to text-to-speech."
```

### Read a File

```bash
./tts document.txt
```

### Read Selected Text

1. Highlight text in any application
2. Press `Ctrl+Alt+S`
3. Listen to the speech

### Stop Speaking

Press `Ctrl+Alt+Q` or `Ctrl+C` in the terminal.

---

## 4. Basic Usage

### Input Sources

The application accepts multiple input types:

| Source | Syntax | Example |
|--------|--------|---------|
| Direct text | `./tts "text"` | `./tts "Hello world"` |
| Text file | `./tts path/to/file.txt` | `./tts notes.txt` |
| PDF file | `./tts document.pdf` | `./tts report.pdf` |
| URL | `./tts https://...` | `./tts https://example.com/article` |
| Stdin | `echo "text" \| ./tts -` | `cat file.txt \| ./tts -` |
| Clipboard | `./tts --get-clipboard` | Returns clipboard text |

### Interactive Mode

Run without arguments for interactive input:

```bash
./tts
```

```
Interactive mode - 'quit' to exit
> Hello, this is interactive mode.
> Type any text and press enter to hear it spoken.
> quit
```

### Speed Control

```bash
# Slow (good for proofreading)
./tts "Reading slowly" --speed slow

# Normal (default)
./tts "Normal speed" --speed normal

# Fast (good for skimming)
./tts "Reading quickly" --speed fast
```

### Language Selection

```bash
# US English (default)
./tts "Hello" --lang en-us

# British English
./tts "Hello" --lang en-uk

# Tamil
./tts "Hello" --lang ta
```

---

## 5. Command Reference

### Full Command Syntax

```
./tts [SOURCE...] [OPTIONS]
```

### Positional Arguments

| Argument | Description |
|----------|-------------|
| `SOURCE` | Text to speak, file path, URL, or `-` for stdin. Multiple words are combined. If omitted, enters interactive mode. |

### Options

#### Speech Options

| Short | Long | Values | Default | Description |
|-------|------|--------|---------|-------------|
| `-l` | `--lang` | `en-us`, `en-uk`, `ta` | `en-us` | Language/voice selection |
| `-s` | `--speed` | `slow`, `normal`, `fast` | `normal` | Speech rate adjustment |

#### System Options

| Short | Long | Description |
|-------|------|-------------|
| `-v` | `--verbose` | Show detailed progress information |
| | `--no-cache` | Bypass cache, regenerate audio |
| | `--clear-cache` | Delete all cached audio files |
| | `--list-engines` | Show available TTS engines |
| | `--get-clipboard` | Print clipboard text and exit |
| `-h` | `--help` | Show help message |

### Examples

```bash
# Basic usage
./tts "Simple text"

# File with verbose output
./tts document.txt -v

# British English, slow speed
./tts proofread.txt -l en-uk -s slow

# Pipe content
cat README.md | ./tts -

# Force fresh generation
./tts "Test" --no-cache

# Check clipboard content
./tts --get-clipboard
```

---

## 6. Keyboard Shortcuts

### Default Shortcuts

| Shortcut | Action | Description |
|----------|--------|-------------|
| `Ctrl+Alt+S` | Speak Selection | Reads text from clipboard/selection |
| `Ctrl+Alt+Q` | Stop Speaking | Stops current playback |

### How Selection Works

**X11 (Traditional):**
- Highlight text (primary selection) OR
- Copy text with Ctrl+C (clipboard selection)
- Press `Ctrl+Alt+S`

**Wayland:**
- Copy text with Ctrl+C
- Press `Ctrl+Alt+S`

### Installing Shortcuts

```bash
python3 configure.py
```

The script auto-detects your desktop environment:
- GNOME: Uses gsettings
- KDE: Modifies kglobalshortcutsrc
- XFCE: Uses xfconf
- Sway/Hyprland: Modifies config files

### Manual Shortcut Setup

If automatic setup fails:

**GNOME:**
1. Settings → Keyboard → Keyboard Shortcuts → Custom Shortcuts
2. Click "Add Shortcut"
3. Name: `Speak Selection`
4. Command: `/path/to/tts/speak_selection.sh`
5. Shortcut: Press `Ctrl+Alt+S`
6. Repeat for `Stop Speaking` → `/path/to/tts/stop_speaking.sh` → `Ctrl+Alt+Q`

**KDE:**
1. System Settings → Shortcuts → Custom Shortcuts
2. Edit → New → Global Shortcut → Command/URL
3. Trigger: `Ctrl+Alt+S`
4. Action: `/path/to/tts/speak_selection.sh`

---

## 7. Languages and Voices

### Available Languages

| Code | Language | Voice (Edge TTS) | Voice (gTTS Fallback) |
|------|----------|------------------|----------------------|
| `en-us` | English (US) | en-US-GuyNeural | English (US) |
| `en-uk` | English (UK) | en-GB-RyanNeural | English (UK) |
| `ta` | Tamil | ta-IN-ValluvarNeural | Tamil |

### Language Aliases

The following aliases are accepted:

| Alias | Maps To |
|-------|---------|
| `en` | `en-us` |
| `en-gb` | `en-uk` |

### Speed Adjustments

| Speed | Rate Change |
|-------|-------------|
| `slow` | -25% |
| `normal` | 0% |
| `fast` | +25% |

### Engine Priority

The application tries engines in order:

1. **Edge TTS** (Primary) - Microsoft Azure neural voices, highest quality
2. **gTTS** (Fallback) - Google Text-to-Speech, good quality
3. **eSpeak** (Last resort) - Synthesized voice, basic quality

---

## 8. Text Processing

### Automatic Cleaning

The application automatically removes:

- URLs: `https://example.com/path`
- Email addresses: `user@example.com`
- Excess whitespace
- Common PDF artifacts

### Text Chunking

Long text is split into chunks for processing:

- **Chunk Size**: 500 characters maximum
- **Boundary Detection**: Splits at sentence endings (`. ! ? ; : ,`)
- **Purpose**: Ensures smooth playback and better caching

### Supported File Formats

| Format | Extension | Dependencies |
|--------|-----------|--------------|
| Plain Text | `.txt` | None |
| Markdown | `.md` | None |
| PDF | `.pdf` | `poppler-utils` |

### Web Content

When a URL is provided:
1. Fetches the page content
2. Removes scripts, styles, navigation
3. Extracts main text content
4. Falls back to lynx/curl/wget if available

---

## 9. Caching System

### How Caching Works

Audio is cached for instant replay:

```
Cache Key = MD5(text + language + speed)
Cache Location = ~/.cache/tts_app/
```

### Cache Examples

Same text, different settings = different cache:

```bash
./tts "Hello"              # Cache: abc123.mp3
./tts "Hello" --lang en-uk # Cache: def456.mp3 (different cache)
./tts "Hello"              # Cache: abc123.mp3 (reused)
```

### Managing Cache

```bash
# View cache size
du -sh ~/.cache/tts_app/

# Clear all cached audio
./tts --clear-cache

# Bypass cache for one run
./tts "Test" --no-cache

# Manual cleanup (delete files older than 30 days)
find ~/.cache/tts_app/ -name "*.mp3" -mtime +30 -delete
```

---

## 10. Advanced Usage

### Piping Content

```bash
# Read command output
date | ./tts -

# Read multiple files
cat chapter1.txt chapter2.txt | ./tts -

# Read from another command
curl -s https://example.com/api/text | ./tts -
```

### Scripting

```bash
#!/bin/bash
# notification.sh - Speak system notifications

MESSAGE="$1"
/path/to/tts "$MESSAGE" &
```

### Cron Job Example

```bash
# Speak a reminder every hour
0 * * * * /path/to/tts "It is now $(date +'%I %M %p')"
```

### Integration with Other Tools

```bash
# Read git commit messages
git log -1 --pretty=%B | ./tts -

# Read system logs
tail -n 5 /var/log/syslog | ./tts -

# Read clipboard history (if using clipman)
./tts "$(xclip -o -selection clipboard)"
```

---

## 11. Daemon Mode

The application includes a daemon for lower latency:

### Starting the Daemon

```bash
# Start daemon (foreground)
./ttsc --daemon

# Start daemon (background)
./ttsc --daemon --fork

# Start via systemd
systemctl --user start tts-daemon
systemctl --user enable tts-daemon  # Auto-start on login
```

### Using the Daemon

```bash
# Speak via daemon
./ttsc speak "Hello from the daemon"

# Stop speaking
./ttsc stop

# Check status
./ttsc status
```

### Daemon Advantages

| Feature | CLI Mode | Daemon Mode |
|---------|----------|-------------|
| Startup time | ~500ms | ~50ms |
| Process overhead | New process each time | Single process |
| Queue management | None | Built-in |
| IPC support | No | D-Bus/Socket |

---

## 12. Troubleshooting

### No Audio Output

**Symptoms:** Application runs but no sound is heard.

**Solutions:**

1. Check system audio:
   ```bash
   speaker-test -t sine -f 440 -l 1
   ```

2. Verify mpg123 works:
   ```bash
   mpg123 ~/.cache/tts_app/*.mp3
   ```

3. Check audio player detection:
   ```bash
   ./tts --list-engines
   ```

4. Install mpg123:
   ```bash
   sudo apt install mpg123
   ```

### Loud Hissing/Static

**Cause:** Wrong audio player being used.

**Solution:** Ensure mpg123 is installed and takes priority:
```bash
which mpg123  # Should return /usr/bin/mpg123
```

### "No audio player found" Error

**Solutions:**
```bash
# Install mpg123 (recommended)
sudo apt install mpg123

# Alternative: Install VLC
sudo apt install vlc

# Alternative: Install ffmpeg
sudo apt install ffmpeg
```

### Clipboard Not Working

**X11:**
```bash
# Install xclip
sudo apt install xclip

# Test clipboard
xclip -o -selection clipboard
```

**Wayland:**
```bash
# Install wl-clipboard
sudo apt install wl-clipboard

# Test clipboard
wl-paste
```

### Keyboard Shortcuts Not Working

1. **Verify installation:**
   ```bash
   python3 configure.py
   ```

2. **Log out and back in** (GNOME sometimes requires this)

3. **Check for conflicts:**
   - Open Settings → Keyboard → Shortcuts
   - Look for duplicate `Ctrl+Alt+S` bindings

4. **Manual test:**
   ```bash
   ~/.local/bin/tts-speak
   ```

### "edge-tts not found" Error

**Cause:** Virtual environment not activated or dependencies not installed.

**Solutions:**
```bash
# Reinstall dependencies
./.venv/bin/pip install -r requirements.txt

# Verify installation
./.venv/bin/pip show edge-tts
```

### Slow First Playback

**Cause:** First-time audio generation requires network access.

**Solutions:**
- This is normal behavior
- Subsequent plays use cache (instant)
- Pre-cache common phrases if needed

### Cache Corruption

**Symptoms:** Garbled audio or errors.

**Solution:**
```bash
./tts --clear-cache
```

---

## 13. Configuration Files

### File Locations

| File | Location | Purpose |
|------|----------|---------|
| Cache | `~/.cache/tts_app/` | Generated audio files |
| Desktop Entry | `~/.local/share/applications/tts.desktop` | Application menu entry |
| Wrapper Scripts | `~/.local/bin/tts*` | System-wide commands |
| Systemd Service | `~/.config/systemd/user/tts-daemon.service` | Daemon auto-start |

### Environment Variables

None required. The application auto-detects settings.

### Customizing Voices

Edit `app.py` to add new languages:

```python
LANG_CONFIG = {
    "en-us": {"name": "English (US)", "voice": "en-US-GuyNeural", "fallback_tld": "us"},
    "en-uk": {"name": "English (UK)", "voice": "en-GB-RyanNeural", "fallback_tld": "co.uk"},
    "ta": {"name": "Tamil", "voice": "ta-IN-ValluvarNeural", "fallback_tld": None},
    # Add new languages here
    "es": {"name": "Spanish", "voice": "es-ES-AlvaroNeural", "fallback_tld": "es"},
}
```

Find available Edge TTS voices:
```bash
./.venv/bin/edge-tts --list-voices
```

---

## 14. Uninstallation

### Remove System Integration

```bash
# Remove shortcuts and desktop entry
rm ~/.local/share/applications/tts.desktop
rm ~/.local/bin/tts
rm ~/.local/bin/tts-stop
rm ~/.local/bin/tts-speak
systemctl --user disable tts-daemon
rm ~/.config/systemd/user/tts-daemon.service
```

### Remove Cache

```bash
rm -rf ~/.cache/tts_app/
```

### Remove Application

```bash
rm -rf /path/to/tts/
```

---

## Appendix: Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│                    TTS QUICK REFERENCE                       │
├─────────────────────────────────────────────────────────────┤
│  BASIC USAGE                                                 │
│  ./tts "text"              Speak text directly               │
│  ./tts file.txt            Read file aloud                   │
│  ./tts -                   Read from stdin                   │
├─────────────────────────────────────────────────────────────┤
│  OPTIONS                                                     │
│  -l, --lang LANG           Language: en-us, en-uk, ta        │
│  -s, --speed SPEED         Speed: slow, normal, fast         │
│  -v, --verbose             Show progress                     │
│  --no-cache                Skip cache                        │
│  --clear-cache             Delete all cached audio           │
├─────────────────────────────────────────────────────────────┤
│  KEYBOARD SHORTCUTS                                          │
│  Ctrl+Alt+S                Speak selection                   │
│  Ctrl+Alt+Q                Stop speaking                     │
├─────────────────────────────────────────────────────────────┤
│  EXAMPLES                                                    │
│  ./tts doc.txt -l en-uk -s slow                             │
│  cat notes.txt | ./tts -                                     │
│  ./tts "Done" && echo "Task complete"                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Support

For issues and feature requests, please check the project documentation or submit an issue on the project repository.
