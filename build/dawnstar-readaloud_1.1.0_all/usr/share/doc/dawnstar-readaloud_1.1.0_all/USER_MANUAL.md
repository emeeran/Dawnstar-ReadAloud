# TTS Application - Complete User Manual

A comprehensive guide to the Enhanced Text-to-Speech application for Linux.

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Installation](#2-installation)
3. [Quick Start](#3-quick-start)
4. [Basic Usage](#4-basic-usage)
5. [Command Reference](#5-command-reference)
6. [Configuration](#6-configuration)
7. [Keyboard Shortcuts](#7-keyboard-shortcuts)
8. [Languages and Voices](#8-languages-and-voices)
9. [Text Processing](#9-text-processing)
10. [Caching System](#10-caching-system)
11. [Advanced Usage](#11-advanced-usage)
12. [Troubleshooting](#12-troubleshooting)
13. [File Locations](#13-file-locations)
14. [Uninstallation](#14-uninstallation)

---

## 1. Introduction

### Overview

The Enhanced TTS Application is a lightweight, neural-network-based text-to-speech system for Linux. It converts written text into natural-sounding speech using Microsoft Azure's neural voices via Edge TTS, with automatic fallback to Google TTS if needed.

### Key Features

| Feature | Description |
|---------|-------------|
| **Neural Voices** | High-quality AI-generated speech via Edge TTS |
| **Smart Caching** | Instant replay with LRU cache and size limits |
| **Configuration File** | Persistent preferences in `~/.config/tts/config.yaml` |
| **Multi-Language** | US English, UK English, and Tamil support |
| **System Integration** | Global keyboard shortcuts for any application |
| **Multiple Input Sources** | Files, PDFs, EPUBs, URLs, clipboard, stdin |
| **Desktop Notifications** | Visual feedback for long texts |
| **Progress Indication** | Chunk counter for multi-segment playback |
| **Cross-Platform Clipboard** | Works on X11 and Wayland |

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

# Optional: For desktop notifications
sudo apt install -y libnotify-bin
```

**Package Descriptions:**

| Package | Purpose | Required |
|---------|---------|----------|
| `mpg123` | MP3 audio playback | Yes |
| `xclip` | Clipboard access (X11) | Yes* |
| `wl-clipboard` | Clipboard access (Wayland) | Yes* |
| `poppler-utils` | PDF text extraction | No |
| `lynx` | Web content extraction | No |
| `libnotify-bin` | Desktop notifications | No |

*Either xclip (X11) or wl-clipboard (Wayland) is required for keyboard shortcuts.

### Step 2: Create Virtual Environment

```bash
cd /path/to/tts
python3 -m venv .venv
```

### Step 3: Install Python Dependencies

```bash
# Install the package in editable mode
./.venv/bin/pip install -e .

# Or install with development dependencies (for contributors)
./.venv/bin/pip install -e ".[dev]"
```

**Python Packages:**

| Package | Purpose |
|---------|---------|
| `edge-tts` | Microsoft Edge neural TTS engine |
| `gtts` | Google TTS (fallback engine) |
| `ebooklib` | EPUB ebook support |
| `beautifulsoup4` | HTML parsing for EPUB extraction |
| `pyyaml` | Configuration file parsing |
| `pyperclip` | Cross-platform clipboard access |
| `pypdf` | PDF text extraction |

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

### Read an E-book

```bash
./tts mybook.epub
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
| EPUB file | `./tts book.epub` | `./tts novel.epub` |
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

### Progress Indication

For longer texts, progress is shown automatically:

```bash
./tts long_document.txt
[1/5] [2/5] [3/5] [4/5] [5/5]
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

### Speech Options

| Short | Long | Values | Default | Description |
|-------|------|--------|---------|-------------|
| `-l` | `--lang` | `en-us`, `en-uk`, `ta` | config | Language/voice selection |
| `-s` | `--speed` | `slow`, `normal`, `fast` | config | Speech rate adjustment |
| `-v` | `--verbose` | - | - | Show detailed progress information |

### Cache Options

| Long | Description |
|------|-------------|
| `--no-cache` | Bypass cache, regenerate audio |
| `--clear-cache` | Delete all cached audio files |
| `--cache-stats` | Show cache size and statistics |

### Configuration Options

| Long | Description |
|------|-------------|
| `--show-config` | Display current configuration |
| `--generate-config` | Generate sample config file |
| `--config-path` | Show configuration file path |
| `--reset-config` | Reset configuration to defaults |

### System Options

| Long | Description |
|------|-------------|
| `--list-engines` | Show available TTS engines |
| `--get-clipboard` | Print clipboard text and exit |
| `-h`, `--help` | Show help message |

### Examples

```bash
# Basic usage
./tts "Simple text"

# File with verbose output
./tts document.txt -v

# British English, slow speed
./tts proofread.txt -l en-uk -s slow

# Read an e-book
./tts mybook.epub

# Check cache statistics
./tts --cache-stats

# Show current configuration
./tts --show-config

# Generate sample config
./tts --generate-config > ~/.config/tts/config.yaml

# Pipe content
cat README.md | ./tts -

# Force fresh generation
./tts "Test" --no-cache
```

---

## 6. Configuration

### Configuration File

The application uses a YAML configuration file for persistent settings:

**Location:** `~/.config/tts/config.yaml`

### Creating Configuration

```bash
# Generate sample configuration
./tts --generate-config > ~/.config/tts/config.yaml

# Or create manually
mkdir -p ~/.config/tts
nano ~/.config/tts/config.yaml
```

### Configuration Options

```yaml
# TTS Application Configuration
# ~/.config/tts/config.yaml

# Language: en-us, en-uk, ta
language: en-us

# Speed: slow, normal, fast
speed: normal

# Enable audio caching
cache_enabled: true

# Maximum cache size in megabytes
cache_max_size_mb: 500

# Show verbose output
verbose: false

# Show desktop notifications
notifications: true

# Show progress for long texts
progress: true

# Preferred engine: edge, gtts, espeak (null = auto)
default_engine: null
```

### Configuration Priority

Settings are applied in this order (later overrides earlier):

1. Built-in defaults
2. Configuration file
3. Command-line arguments

### Viewing Configuration

```bash
# Show current configuration with source
./tts --show-config

# Show config file path
./tts --config-path

# Reset to defaults
./tts --reset-config
```

### Example Output

```
$ ./tts --show-config
Configuration file: /home/user/.config/tts/config.yaml
Source: file

  language: en-uk
  speed: normal
  cache_enabled: True
  cache_max_size_mb: 500
  verbose: False
  notifications: True
  progress: True
  default_engine: None
```

---

## 7. Keyboard Shortcuts

### Default Shortcuts

| Shortcut | Action | Description |
|----------|--------|-------------|
| `Ctrl+Alt+S` | Speak Selection | Reads text from clipboard/selection |
| `Ctrl+Alt+Q` | Stop Speaking | Stops current playback |

### How Selection Works

**X11 (Traditional):**
1. Highlight text with mouse (primary selection) - **recommended**
2. Or copy text with Ctrl+C (clipboard selection)
3. Press `Ctrl+Alt+S`
4. The highlighted text is prioritized over copied text

**Wayland:**
1. Copy text with Ctrl+C
2. Press `Ctrl+Alt+S`

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

---

## 8. Languages and Voices

### Available Languages

| Code | Language | Voice (Edge TTS) | Voice (gTTS Fallback) |
|------|----------|------------------|----------------------|
| `en-us` | English (US) | en-US-GuyNeural | English (US) |
| `en-uk` | English (UK) | en-GB-RyanNeural | English (UK) |
| `ta` | Tamil | ta-IN-ValluvarNeural | Tamil |

### Language Aliases

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

## 9. Text Processing

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

| Format | Extension | Dependencies | Features |
|--------|-----------|--------------|----------|
| Plain Text | `.txt` | None | Direct reading |
| Markdown | `.md` | None | Direct reading |
| PDF | `.pdf` | `pypdf` | **Smart skip** (finds Chapter 1/Intro) |
| EPUB | `.epub` | `ebooklib`, `bs4` | **Smart skip** (skips TOC/copyright) |
| Web Article | `URL` | `bs4` | **Ad-free** (extracts main text) |

### EPUB & PDF Smart Skip

The application automatically identifies and skips "front matter" (Title pages, Copyright, Table of Contents, Dedications) to get straight to the content:

- **EPUB**: Scans internal sections and skips those with low word counts or matching "front matter" patterns until the first significant chapter is found.
- **PDF**: Scans the first 50 pages for chapter headings or introduction markers. If none are found, it skips a small percentage of the initial pages as a fallback.

```bash
./tts mybook.epub  # Starts reading from Chapter 1
./tts report.pdf   # Skips the preface and TOC
```

### Web Content

When a URL is provided, the application performs high-quality article extraction:
1. **Ad Removal**: Decomposes ads, banners, and overlays.
2. **Nav Cleanup**: Skips site-wide navigation, footers, and sidebars.
3. **TOC Filtering**: Identifies and removes internal "Table of Contents" blocks.
4. **Main Content**: Intelligently identifies the article body using semantic tags and site-specific rules (e.g., Wikipedia, blogs).

```bash
./tts https://en.wikipedia.org/wiki/Artificial_intelligence
```

---

## 10. Caching System

### How Caching Works

Audio is cached for instant replay:

```
Cache Key = MD5(text + language + speed)
Cache Location = ~/.cache/tts_app/
```

### LRU Cache Management

The cache automatically manages size:

- **Default Limit**: 500 MB
- **Eviction Policy**: Least Recently Used (LRU)
- **Configuration**: Set `cache_max_size_mb` in config file

When the cache exceeds the limit, oldest files are removed automatically.

### Cache Statistics

```bash
$ ./tts --cache-stats
Cache Statistics:
  Files: 45
  Size: 2.35 MB / 500 MB
  Location: /home/user/.cache/tts_app
```

### Managing Cache

```bash
# View cache statistics
./tts --cache-stats

# Clear all cached audio
./tts --clear-cache

# Bypass cache for one run
./tts "Test" --no-cache

# Manual cleanup (delete files older than 30 days)
find ~/.cache/tts_app/ -name "*.mp3" -mtime +30 -delete
```

---

## 11. Advanced Usage

### Desktop Notifications

For longer texts, desktop notifications show playback status:

- **Start**: "Speaking N segments..."
- **Complete**: "Finished speaking"
- **Error**: "Playback failed"

Configure in `~/.config/tts/config.yaml`:

```yaml
notifications: true   # Enable notifications
```

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

### Daemon Mode (Low Latency)

For frequent speech synthesis, use the daemon mode for lower latency:

**Latency Comparison:**
| Mode | Startup Time | Use Case |
|------|-------------|----------|
| CLI (`./tts`) | ~500ms | Occasional use |
| Daemon (`ttsc`) | ~50ms | Frequent use, keyboard shortcuts |

#### Starting the Daemon

```bash
# Start daemon in foreground (Ctrl+C to stop)
./ttsc daemon

# Start daemon in background
./ttsc daemon --fork

# Or using Python module
./.venv/bin/python -m ttsd
```

#### Using the Daemon

```bash
# Check daemon status
./ttsc status

# Speak text
./ttsc speak "Hello from the daemon"

# Read a file via daemon
./ttsc speak document.txt

# Read a URL via daemon
./ttsc speak https://example.com

# Speak clipboard selection
./ttsc selection

# Control playback
./ttsc pause
./ttsc resume
./ttsc stop

# Stop the daemon
./ttsc stop-daemon
```

#### Daemon Commands

| Command | Description |
|---------|-------------|
| `daemon` | Start the daemon |
| `status` | Show daemon status |
| `speak TEXT` | Queue text for speaking |
| `selection` | Speak clipboard content |
| `pause` | Pause current playback |
| `resume` | Resume paused playback |
| `stop` | Stop current playback |
| `stop-daemon` | Stop the daemon |

#### When to Use Daemon Mode

**Use daemon mode when:**
- You use keyboard shortcuts frequently
- You trigger speech dozens of times per hour
- You need minimal latency

**Use CLI mode when:**
- You occasionally need TTS
- You want the simplest setup
- You're running scripts that need isolation

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
sudo apt install xclip
xclip -o -selection clipboard
```

**Wayland:**
```bash
sudo apt install wl-clipboard
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

### EPUB Not Working

**Symptoms:** Error reading EPUB files.

**Solution:** Install required dependencies:
```bash
./.venv/bin/pip install ebooklib beautifulsoup4
```

### Notifications Not Showing

**Cause:** `notify-send` not installed.

**Solution:**
```bash
sudo apt install libnotify-bin
```

Or disable notifications in config:
```yaml
notifications: false
```

### Cache Growing Too Large

**Solution:**
```bash
# Check cache size
./tts --cache-stats

# Reduce limit in config
# Edit ~/.config/tts/config.yaml
cache_max_size_mb: 200

# Or clear cache
./tts --clear-cache
```

### "edge-tts not found" Error

**Cause:** Virtual environment not activated or dependencies not installed.

**Solutions:**
```bash
# Reinstall dependencies
./.venv/bin/pip install -e .

# Verify installation
./.venv/bin/pip show edge-tts
```

### Configuration Not Loading

**Symptoms:** Settings in config file not being applied.

**Solutions:**

1. Check config file path:
   ```bash
   ./tts --config-path
   ```

2. Verify YAML syntax:
   ```bash
   python3 -c "import yaml; yaml.safe_load(open('~/.config/tts/config.yaml'))"
   ```

3. Show current config:
   ```bash
   ./tts --show-config
   ```

---

## 13. File Locations

| File | Location | Purpose |
|------|----------|---------|
| Configuration | `~/.config/tts/config.yaml` | User preferences |
| Cache | `~/.cache/tts_app/` | Generated audio files |
| Desktop Entry | `~/.local/share/applications/tts.desktop` | Application menu entry |
| Wrapper Scripts | `~/.local/bin/tts*` | System-wide commands |

---

## 14. Uninstallation

### Remove System Integration

```bash
rm ~/.local/share/applications/tts.desktop
rm ~/.local/bin/tts
rm ~/.local/bin/tts-stop
rm ~/.local/bin/tts-speak
```

### Remove Configuration and Cache

```bash
rm -rf ~/.config/tts/
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
│  ./tts book.epub           Read e-book                       │
│  ./tts -                   Read from stdin                   │
├─────────────────────────────────────────────────────────────┤
│  OPTIONS                                                     │
│  -l, --lang LANG           Language: en-us, en-uk, ta        │
│  -s, --speed SPEED         Speed: slow, normal, fast         │
│  -v, --verbose             Show progress                     │
│  --no-cache                Skip cache                        │
│  --cache-stats             Show cache statistics             │
│  --show-config             Display configuration             │
├─────────────────────────────────────────────────────────────┤
│  KEYBOARD SHORTCUTS                                          │
│  Ctrl+Alt+S                Speak selection                   │
│  Ctrl+Alt+Q                Stop speaking                     │
├─────────────────────────────────────────────────────────────┤
│  CONFIG FILE: ~/.config/tts/config.yaml                      │
│  language: en-us                                             │
│  speed: normal                                               │
│  cache_max_size_mb: 500                                      │
│  notifications: true                                         │
│  progress: true                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Support

For issues and feature requests, please check the project documentation or submit an issue on the project repository.
