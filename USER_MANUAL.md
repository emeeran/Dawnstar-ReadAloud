# Dawnstar ReadAloud — User Manual

Complete guide to the Dawnstar ReadAloud text-to-speech application for Linux.

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Installation](#2-installation)
3. [Quick Start](#3-quick-start)
4. [Keyboard Shortcuts](#4-keyboard-shortcuts)
5. [Command-Line Usage](#5-command-line-usage)
6. [Input Sources](#6-input-sources)
7. [Content Extraction](#7-content-extraction)
8. [Languages and Voices](#8-languages-and-voices)
9. [Caching System](#9-caching-system)
10. [Configuration](#10-configuration)
11. [Daemon Mode](#11-daemon-mode)
12. [Desktop Integration](#12-desktop-integration)
13. [Advanced Usage](#13-advanced-usage)
14. [Troubleshooting](#14-troubleshooting)
15. [File Locations](#15-file-locations)
16. [Uninstallation](#16-uninstallation)

---

## 1. Introduction

### Overview

Dawnstar ReadAloud converts text into natural-sounding speech using Microsoft Azure neural voices. It runs as a command-line tool, a background daemon, or through global keyboard shortcuts that work in any application.

### Key Features

| Feature | Description |
|---------|-------------|
| Neural voices | Microsoft Azure Edge TTS with automatic fallback to Google TTS and eSpeak |
| Global shortcuts | Speak from cursor, read documents, speak selection, stop — from any app |
| Source detection | Detects the focused window's file path or URL automatically |
| Smart extraction | Skips ads and navigation in web pages, front matter in PDFs/EPUBs |
| Smart caching | MD5-keyed LRU cache with configurable size limit |
| Multi-language | US English, UK English, Tamil |
| Multiple sources | Direct text, files, PDF, EPUB, URLs, clipboard, stdin |
| Daemon mode | Background service for low-latency frequent use |
| Desktop integration | Application menu entry, wrapper scripts, systemd service |

### System Requirements

| Requirement | Details |
|-------------|---------|
| Operating system | Linux (Ubuntu/Debian recommended) |
| Python | 3.12 or higher |
| Audio | Working audio output |
| Desktop | GNOME, KDE, XFCE, Sway, or Hyprland (for keyboard shortcuts) |

---

## 2. Installation

### System Dependencies

```bash
sudo apt update
sudo apt install -y mpg123 xclip poppler-utils libnotify-bin
```

| Package | Purpose | Required |
|---------|---------|----------|
| `mpg123` | MP3 audio playback | Yes |
| `xclip` | Clipboard access (X11) | Yes* |
| `wl-clipboard` | Clipboard access (Wayland) | Yes* |
| `poppler-utils` | PDF text extraction | No |
| `libnotify-bin` | Desktop notifications | No |

\* Either xclip (X11) or wl-clipboard (Wayland) is required for keyboard shortcuts.

### Python Setup

```bash
cd /path/to/Dawnstar-ReadAloud

# Create virtual environment
python3 -m venv .venv

# Install the package
./.venv/bin/pip install -e .

# Or with development tools (for contributors)
./.venv/bin/pip install -e ".[dev]"
```

### Verify Installation

```bash
./tts --list-engines
```

Expected output:

```
Available TTS engines:
  edge: ok
  gtts: ok
  espeak: not available
```

### System Integration

```bash
python3 configure.py
```

This installs keyboard shortcuts, desktop menu entry, wrapper scripts in `~/.local/bin/`, and an optional systemd user service.

---

## 3. Quick Start

### Speak Text Directly

```bash
./tts "Hello, world! Welcome to text-to-speech."
```

### Read a File

```bash
./tts document.txt
./tts book.epub
./tts report.pdf
```

### Read from Cursor (Global Shortcut)

1. Place your text cursor in any text field or editor
2. Press **Shift+Alt+F**
3. The app reads from your cursor position to the end

### Read Active Document (Global Shortcut)

1. Open a PDF, EPUB, or web page in any viewer or browser
2. Press **Shift+Alt+D**
3. The app detects the source and reads from the beginning

### Speak Selection (Global Shortcut)

1. Highlight text in any application
2. Press **Shift+Alt+C**
3. The selected text is spoken

### Stop Speaking

Press **Shift+Alt+Q** (global) or **Ctrl+C** (in terminal).

---

## 4. Keyboard Shortcuts

### Shortcuts Overview

| Shortcut | Action | Script |
|----------|--------|--------|
| `Shift+Alt+F` | Speak from cursor | `speak_from_cursor.sh` |
| `Shift+Alt+D` | Read active document | `speak_active_doc.sh` |
| `Shift+Alt+C` | Speak selection (clipboard) | `speak_selection.sh` |
| `Shift+Alt+Q` | Stop speaking | `stop_speaking.sh` |

### Speak from Cursor (Shift+Alt+F)

Reads text starting from your cursor position in the focused application.

**How it works:**

1. Tries AT-SPI accessibility APIs to extract text from the focused text container at the cursor position
2. Falls back to primary selection (highlighted text) via xclip
3. Speaks the extracted text through the TTS engine

**Requirements:**

- The application must support AT-SPI (most GTK and Qt apps do)
- Or you can highlight text before pressing the shortcut

**Supported applications:**

- Text editors (GNOME Text Editor, gedit, Kate, VS Code, Typora)
- Terminal emulators
- Browser text fields
- Document viewers (for highlighted text)
- Most GTK/Qt applications

### Read Active Document (Shift+Alt+D)

Detects the document open in the focused window and reads it from the beginning.

**How it works:**

1. Identifies the focused window via xdotool
2. Detects the application type (browser, viewer, editor)
3. Extracts the source:
   - **Browsers**: Simulates Ctrl+L, Ctrl+C to get the URL from the address bar
   - **Document viewers** (Okular, Evince, etc.): Extracts filename from window title, resolves to full path via recently-used files and `/proc` inspection
   - **Text editors**: Extracts file path from window title
   - **PID fallback**: Checks process command-line arguments and open file descriptors
4. Passes the source to `tts <source>` for full content extraction

**Supported applications:**

| Application | Detection Method |
|-------------|-----------------|
| Okular | Window title + PID file descriptors |
| Evince / Atril | Window title + recently-used list |
| Google Chrome | Address bar URL extraction |
| Firefox | Address bar URL extraction |
| Chromium | Address bar URL extraction |
| GNOME Text Editor | Title path extraction |
| Typora | Title path extraction |
| Kate / gedit | Title path extraction |

**For URLs:** The content is fetched and extracting with ad/navigation removal. Supports both static HTML and dynamic JavaScript-rendered pages (via JSON-LD extraction).

**For PDF/EPUB:** Front matter is automatically skipped (preface, TOC, copyright), starting from Chapter 1.

**For Markdown:** Formatting is stripped (headers, bold, links, code blocks) while preserving readable text content.

### Speak Selection (Shift+Alt+C)

Reads text from the clipboard or primary selection.

**X11:**

1. Prioritizes primary selection (text highlighted with mouse)
2. Falls back to clipboard (Ctrl+C)
3. Speaks the text

**Wayland:**

1. Reads from the clipboard (Ctrl+C)
2. Speaks the text

### Stop Speaking (Shift+Alt+Q)

Immediately stops all TTS playback:

1. Kills audio streams via PulseAudio/PipeWire
2. Terminates TTS processes (including Docker containers)
3. Cleans up temporary files

### Installing Shortcuts

```bash
python3 configure.py
```

The script auto-detects your desktop environment and runs the appropriate setup:

| Desktop Environment | Method |
|---------------------|--------|
| GNOME | gsettings custom keybindings |
| KDE Plasma | kglobalshortcutsrc |
| XFCE | xfconf-query |
| Sway | Appends bindsym to config |
| Hyprland | Appends bind to config |

### Manual Shortcut Setup

If automatic setup fails, configure manually:

**GNOME:**

1. Settings → Keyboard → Keyboard Shortcuts → Custom Shortcuts
2. Click "Add Shortcut"
3. Add each shortcut:

| Name | Command | Key |
|------|---------|-----|
| Read Active Document | `/path/to/Dawnstar-ReadAloud/speak_active_doc.sh` | Shift+Alt+S |
| Speak Selection | `/path/to/Dawnstar-ReadAloud/speak_selection.sh` | Shift+Alt+C |
| Stop Speaking | `/path/to/Dawnstar-ReadAloud/stop_speaking.sh` | Shift+Alt+Q |

Replace `/path/to/Dawnstar-ReadAloud` with the actual installation path.

**Sway — manual config:**

```
bindsym Shift+Alt+s exec /path/to/speak_active_doc.sh
bindsym Shift+Alt+c exec /path/to/speak_selection.sh
bindsym Shift+Alt+q exec /path/to/stop_speaking.sh
```

**Hyprland — manual config:**

```
bind = SHIFT ALT, s, exec, /path/to/speak_active_doc.sh
bind = SHIFT ALT, c, exec, /path/to/speak_selection.sh
bind = SHIFT ALT, q, exec, /path/to/stop_speaking.sh
```

---

## 5. Command-Line Usage

### Syntax

```
./tts [SOURCE...] [OPTIONS]
```

### Positional Arguments

| Argument | Description |
|----------|-------------|
| `SOURCE` | Text to speak, file path, URL, or `-` for stdin. Multiple arguments are combined. If omitted, enters interactive mode. |

### Speech Options

| Short | Long | Values | Default | Description |
|-------|------|--------|---------|-------------|
| `-l` | `--lang` | `en-us`, `en-uk`, `ta` | `en-us` | Language and voice |
| `-s` | `--speed` | `slow`, `normal`, `fast` | `normal` | Speech rate |
| `-v` | `--verbose` | — | — | Show detailed progress |

### Cache Options

| Long | Description |
|------|-------------|
| `--no-cache` | Bypass cache, regenerate audio |
| `--clear-cache` | Delete all cached audio files |
| `--cache-stats` | Show cache size and file count |

### Configuration Options

| Long | Description |
|------|-------------|
| `--show-config` | Display current configuration |
| `--generate-config` | Generate sample config file to stdout |
| `--config-path` | Show configuration file path |
| `--reset-config` | Reset configuration to defaults |

### System Options

| Long | Description |
|------|-------------|
| `--list-engines` | Show available TTS engines |
| `--list-voices` | List Edge TTS voices |
| `--get-clipboard` | Print clipboard text and exit |
| `--sentence-file FILE` | Write current sentence to file (for progress notifications) |

### Examples

```bash
# Direct text
./tts "Hello world"

# File with verbose output
./tts document.txt -v

# British English, slow speed (good for proofreading)
./tts proofread.txt -l en-uk -s slow

# Read an e-book (skips front matter)
./tts mybook.epub

# Read a web article (extracts main content)
./tts https://en.wikipedia.org/wiki/Linux

# Read from stdin
cat notes.txt | ./tts -

# Force fresh generation (skip cache)
./tts "Test" --no-cache

# Check cache statistics
./tts --cache-stats

# Show current configuration
./tts --show-config

# Generate a sample config file
./tts --generate-config > ~/.config/tts/config.yaml
```

### Interactive Mode

Run without arguments for a REPL:

```bash
./tts
```

```
Interactive mode - 'quit' to exit
> Hello, this is interactive mode.
> Type any text and press enter to hear it spoken.
> quit
```

---

## 6. Input Sources

### Supported Sources

| Source | Syntax | Notes |
|--------|--------|-------|
| Direct text | `./tts "text"` | Multiple arguments are joined |
| Text file | `./tts file.txt` | Plain text or Markdown |
| PDF file | `./tts document.pdf` | Skips preface/TOC, starts Chapter 1 |
| EPUB file | `./tts book.epub` | Skips front matter |
| URL | `./tts https://...` | Extracts main article (static + dynamic sites) |
| Stdin | `cat file \| ./tts -` | Pipe content |
| Clipboard | `./tts --get-clipboard` | Prints clipboard text |

### File Format Support

| Format | Extension | Dependencies | Features |
|--------|-----------|--------------|----------|
| Plain text | `.txt` | None | Direct reading |
| Markdown | `.md` | None | Headers, links, code cleaned |
| PDF | `.pdf` | `pypdf` | Smart skip to Chapter 1 |
| EPUB | `.epub` | `ebooklib`, `beautifulsoup4` | Smart skip past front matter |
| Web pages | URL | `beautifulsoup4` | Ad-free article, JSON-LD support |

### Multiple Sources

Multiple positional arguments are combined into a single text:

```bash
./tts "Chapter 1:" chapter1.txt "End of chapter."
```

---

## 7. Content Extraction

### Web Content (URLs)

When you provide a URL or press **Shift+Alt+S** with a browser focused, the application extracts the main article content:

1. **JSON-LD extraction** (dynamic sites) — Extracts `articleBody` from schema.org structured data for JavaScript-rendered pages (news sites like Deccan Herald, etc.)
2. **Ad removal** — Decomposes ad containers, banners, and overlays
3. **Navigation cleanup** — Removes headers, footers, sidebars, and widgets
4. **Main content detection** — Identifies the article body using semantic HTML tags (`<article>`, `<main>`, ARIA roles) and content-scoring heuristics
5. **Formatting** — Preserves headings, paragraphs, and blockquotes

```bash
./tts https://www.deccanherald.com/...    # Dynamic JavaScript site
./tts https://en.wikipedia.org/wiki/...   # Static HTML site
```

### PDF Content

PDF files are processed with smart content detection:

1. **TOC detection** — Identifies table of contents pages by dotted leader lines
2. **Chapter detection** — Finds "CHAPTER 1" or numbered headings at page start
3. **Preface skip** — Detects preface/acknowledgments by keywords
4. **Start from Chapter 1** — Begins reading from actual chapter content

```bash
./tts report.pdf    # Skips TOC, preface, starts Chapter 1
```

### EPUB Content

EPUB files are processed similarly:

1. Scans internal sections for front matter patterns
2. Skips title pages, TOC, copyright, dedications, prologue
3. Starts reading from the first content chapter

```bash
./tts novel.epub    # Starts from Chapter 1
```

### Markdown Content

Markdown files are cleaned for natural speech:

1. **Headers** — Removes `#` symbols, preserves text
2. **Links** — Keeps link text, removes URLs: `[text](url)` → `text`
3. **Code** — Removes backticks: `` `code` `` → `code`
4. **Lists** — Removes bullets: `- item` → `item`
5. **Bold/italic** — Removes markers: `**bold**` → `bold`

```bash
./tts README.md     # Strips formatting, reads content
```

### Text Cleaning

All input sources receive automatic text cleaning:

- URLs removed (`https://...`)
- Email addresses removed (`user@example.com`)
- Excess whitespace collapsed (newlines, tabs → single space)
- Common PDF artifacts cleaned
- Markdown formatting simplified
- HTML tags stripped (from JSON-LD extraction)

### Text Chunking

Long texts are split into chunks for processing:

- Maximum chunk size: based on sentence boundaries
- Splits at `.`, `!`, `?`, `;`, `:`, `,`
- Preserves natural speech rhythm
- Enables per-chunk caching

### Sentence Highlighting

When reading documents (Shift+Alt+S), a desktop notification shows the current sentence being spoken:

- **Auto-starts** with document reading
- **Updates** as each new sentence is spoken
- **Replaces** previous notification (no spam)
- **Auto-closes** when finished

**Requirements:** `libnotify-bin` package (installed by default on Ubuntu/Debian)

**Disable:** Close the notification manually or kill the overlay process

---

## 8. Languages and Voices

### Available Languages

| Code | Language | Edge TTS Voice | gTTS Fallback |
|------|----------|---------------|---------------|
| `en-us` | English (US) | en-US-GuyNeural | English (US) |
| `en-uk` | English (UK) | en-GB-RyanNeural | English (UK) |
| `ta` | Tamil | ta-IN-ValluvarNeural | Tamil |

### Language Aliases

| Alias | Maps To |
|-------|---------|
| `en` | `en-us` |
| `en-gb` | `en-uk` |

### Speed Settings

| Speed | Edge TTS Rate | eSpeak WPM |
|-------|---------------|------------|
| `slow` | -25% | 120 |
| `normal` | +0% | 160 |
| `fast` | +25% | 200 |

### Engine Fallback Chain

The application tries engines in order:

1. **Edge TTS** (primary) — Microsoft Azure neural voices, highest quality
2. **gTTS** (fallback) — Google Text-to-Speech, good quality, requires internet
3. **eSpeak** (last resort) — Local synthesis, robotic quality, works offline

Set `default_engine` in the config file to override the automatic selection.

---

## 9. Caching System

### How Caching Works

Generated audio is cached for instant replay:

```
Cache key  = MD5(text + language + speed)
Cache dir  = ~/.cache/tts_app/
File type  = MP3
```

If the same text with the same language and speed settings is requested again, the cached audio plays immediately without regenerating.

### Cache Management

The cache uses a Least Recently Used (LRU) eviction policy:

- **Default limit**: 500 MB (configurable)
- **Eviction**: Oldest files are removed when the limit is exceeded
- **Enforcement**: Cache is checked after each new file is written

### Cache Commands

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

### Example Cache Statistics

```
$ ./tts --cache-stats
Cache Statistics:
  Files: 45
  Size: 2.35 MB / 500 MB
  Location: /home/user/.cache/tts_app
```

---

## 10. Configuration

### Configuration File

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
# Dawnstar ReadAloud Configuration
# ~/.config/tts/config.yaml

# Language: en-us, en-uk, ta
language: en-us

# Speed: slow, normal, fast
speed: normal

# Enable audio caching
cache_enabled: true

# Maximum cache size in megabytes (50-5000)
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

Settings are applied in order (later overrides earlier):

1. Built-in defaults
2. Configuration file (`~/.config/tts/config.yaml`)
3. Command-line arguments (`--lang`, `--speed`, etc.)

### Viewing Configuration

```bash
# Show current config with source
./tts --show-config

# Show config file path
./tts --config-path

# Reset to defaults
./tts --reset-config
```

---

## 11. Daemon Mode

The daemon mode provides low-latency TTS by keeping the engine loaded in memory.

### Latency Comparison

| Mode | Startup | Use Case |
|------|---------|----------|
| CLI (`./tts`) | ~500ms | Occasional use, scripts |
| Daemon (`ttsc`) | ~50ms | Frequent use, keyboard shortcuts |

### Starting the Daemon

```bash
# Start daemon in foreground (Ctrl+C to stop)
./ttsc daemon

# Start daemon in background
./ttsc daemon --fork

# Or via Python module
./.venv/bin/python -m ttsd
```

### Using the Daemon

```bash
# Check daemon status
./ttsc status

# Speak text
./ttsc speak "Hello from the daemon"

# Read a file
./ttsc speak document.txt

# Read a URL
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

### Daemon Commands

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

### When to Use Daemon Mode

**Use daemon mode when:**
- You use keyboard shortcuts frequently
- You trigger speech dozens of times per hour
- You need minimal latency

**Use CLI mode when:**
- You occasionally need TTS
- You want the simplest setup
- You are running scripts that need process isolation

---

## 12. Desktop Integration

### Running configure.py

```bash
python3 configure.py
```

This script sets up:

| Component | Location | Purpose |
|-----------|----------|---------|
| Wrapper scripts | `~/.local/bin/tts*` | System-wide commands |
| Desktop entry | `~/.local/share/applications/tts.desktop` | Application menu |
| Keyboard shortcuts | DE-specific | Global hotkeys |
| Systemd service | `~/.config/systemd/user/tts-daemon.service` | Auto-start daemon |

### Installed Wrapper Scripts

| Script | Path | Maps To |
|--------|------|---------|
| `tts` | `~/.local/bin/tts` | Main TTS command |
| `tts-speak` | `~/.local/bin/tts-speak` | Speak from cursor |
| `tts-doc` | `~/.local/bin/tts-doc` | Read active document |
| `tts-selection` | `~/.local/bin/tts-selection` | Speak selection |
| `tts-stop` | `~/.local/bin/tts-stop` | Stop speaking |

After running configure.py, you can use these commands from anywhere:

```bash
tts "Hello"              # Speak text
tts-doc                  # Read active document (same as Shift+Alt+D)
tts-stop                 # Stop speaking (same as Shift+Alt+Q)
```

### Systemd Service (Optional)

To start the TTS daemon automatically on login:

```bash
systemctl --user enable tts-daemon
```

---

## 13. Advanced Usage

### Scripting

```bash
#!/bin/bash
# Speak a notification
/path/to/tts "$1" &
```

### Cron Jobs

```bash
# Hourly time announcement
0 * * * * /path/to/tts "It is now $(date +'%I %M %p')"
```

### Piping Content

```bash
# Read command output
date | ./tts -

# Combine multiple files
cat chapter1.txt chapter2.txt | ./tts -

# Read from an API
curl -s https://api.example.com/text | ./tts -
```

### Docker

```bash
# Build the image
docker build -t dawnstar-readaloud .

# Run with text
docker run --rm -i --device /dev/snd dawnstar-readaloud "Hello world"

# Run with stdin
echo "Hello from Docker" | docker run --rm -i --device /dev/ssnd dawnstar-readaloud -
```

### Debug Mode

When shortcuts don't work, check the debug log:

```bash
cat /tmp/tts_debug.log
```

Add debug output for source detection:

```bash
python3 get_active_source.py  # See what source is detected for current window
python3 get_accessible_text.py  # See what accessibility APIs return
```

---

## 14. Troubleshooting

### No Audio Output

**Symptoms:** The application runs but no sound is heard.

1. Check system audio:
   ```bash
   speaker-test -t sine -f 440 -l 1
   ```

2. Verify mpg123 works:
   ```bash
   mpg123 ~/.cache/tts_app/*.mp3
   ```

3. Install mpg123:
   ```bash
   sudo apt install mpg123
   ```

### Keyboard Shortcuts Not Working

1. Re-run the setup:
   ```bash
   python3 configure.py
   ```

2. Log out and back in (GNOME may require this)

3. Check for conflicting shortcuts:
   - GNOME: Settings → Keyboard → Keyboard Shortcuts → Custom Shortcuts
   - Look for duplicate `Shift+Alt+F/D/C/Q` bindings

4. Test the script directly:
   ```bash
   bash /path/to/Dawnstar-ReadAloud/speak_from_cursor.sh
   ```

5. Check the debug log:
   ```bash
   cat /tmp/tts_debug.log
   ```

### "Read Active Document" Not Detecting Source

The source detection (`Shift+Alt+D`) may fail if:

1. **The application is not recognized** — Check if the application's window class is in the supported list. Run:
   ```bash
   xdotool getactivewindow | xargs -I{} xprop -id {} WM_CLASS
   ```

2. **The file is not in search paths** — Source detection searches recently-used files, common directories, and the process's open file descriptors. Make sure the file was recently opened.

3. **The window title doesn't contain the filename** — Some applications use custom title formats that the parser doesn't recognize.

Debug the detection:
```bash
python3 get_active_source.py  # Should print a file path or URL
echo $?                       # 0 = success, 1 = no source detected
```

### "Speak from Cursor" Not Working

1. **Accessibility APIs not available** — The application must support AT-SPI. Most GTK and Qt apps do. Try highlighting text first as a fallback.

2. **No text at cursor** — Ensure the cursor is positioned inside a text container with actual text content.

3. **Test accessibility directly:**
   ```bash
   python3 get_accessible_text.py
   ```

### Clipboard Not Working

**X11:**
```bash
sudo apt install xclip
xclip -o -selection clipboard    # Test clipboard
xclip -o -selection primary      # Test primary selection
```

**Wayland:**
```bash
sudo apt install wl-clipboard
wl-paste                         # Test clipboard
```

### EPUB Not Working

Install the required dependencies:

```bash
./.venv/bin/pip install ebooklib beautifulsoup4
```

### PDF Not Working

Install poppler-utils and pypdf:

```bash
sudo apt install poppler-utils
./.venv/bin/pip install pypdf
```

### Notifications Not Showing

```bash
sudo apt install libnotify-bin
```

Or disable in config:

```yaml
notifications: false
```

### Cache Growing Too Large

```bash
./tts --cache-stats     # Check current size
./tts --clear-cache     # Clear everything
```

Or reduce the limit in `~/.config/tts/config.yaml`:

```yaml
cache_max_size_mb: 200
```

### "edge-tts not found" Error

Reinstall Python dependencies:

```bash
./.venv/bin/pip install -e .
./.venv/bin/pip show edge-tts
```

### Configuration Not Loading

1. Check the config file path:
   ```bash
   ./tts --config-path
   ```

2. Verify YAML syntax:
   ```bash
   python3 -c "import yaml; yaml.safe_load(open('$HOME/.config/tts/config.yaml'))"
   ```

3. Show current config:
   ```bash
   ./tts --show-config
   ```

---

## 15. File Locations

| File | Location | Purpose |
|------|----------|---------|
| Configuration | `~/.config/tts/config.yaml` | User preferences |
| Cache | `~/.cache/tts_app/` | Generated audio files (MP3) |
| Desktop entry | `~/.local/share/applications/tts.desktop` | Application menu |
| Wrapper scripts | `~/.local/bin/tts*` | System-wide commands |
| Systemd service | `~/.config/systemd/user/tts-daemon.service` | Daemon auto-start |
| Debug log | `/tmp/tts_debug.log` | Shortcut activity log |
| Sentence state | `/tmp/tts_cursor_state/` | Current sentence tracking |
| Daemon socket | `/tmp/tts-daemon.sock` | IPC socket |

---

## 16. Uninstallation

### Remove System Integration

```bash
rm ~/.local/share/applications/tts.desktop
rm ~/.local/bin/tts
rm ~/.local/bin/tts-stop
rm ~/.local/bin/tts-speak
rm ~/.local/bin/tts-doc
rm ~/.local/bin/tts-selection
rm ~/.config/systemd/user/tts-daemon.service
```

### Remove Configuration and Cache

```bash
rm -rf ~/.config/tts/
rm -rf ~/.cache/tts_app/
```

### Remove Application

```bash
rm -rf /path/to/Dawnstar-ReadAloud/
```

---

## Quick Reference Card

```
┌──────────────────────────────────────────────────────────────────┐
│                    DAWNSTAR READALOUD                             │
│                    Quick Reference                                │
├──────────────────────────────────────────────────────────────────┤
│  KEYBOARD SHORTCUTS                                              │
│  Shift+Alt+F    Speak from cursor position                       │
│  Shift+Alt+D    Read active document (PDF, EPUB, URL)            │
│  Shift+Alt+C    Speak selected/highlighted text                  │
│  Shift+Alt+Q    Stop speaking                                    │
├──────────────────────────────────────────────────────────────────┤
│  CLI USAGE                                                       │
│  ./tts "text"              Speak text directly                   │
│  ./tts file.txt            Read file                             │
│  ./tts book.epub           Read e-book (skips front matter)      │
│  ./tts report.pdf          Read PDF (skips preface)              │
│  ./tts https://...         Read web article (skips ads)          │
│  ./tts -                   Read from stdin                       │
│  ./tts                      Interactive mode                     │
├──────────────────────────────────────────────────────────────────┤
│  OPTIONS                                                         │
│  -l, --lang LANG           Language: en-us, en-uk, ta            │
│  -s, --speed SPEED         Speed: slow, normal, fast             │
│  -v, --verbose             Show detailed progress                │
│  --no-cache                Skip cache, regenerate audio          │
│  --cache-stats             Show cache statistics                 │
│  --clear-cache             Delete all cached audio               │
│  --show-config             Display configuration                 │
│  --generate-config         Generate sample config file           │
│  --list-engines            Show available TTS engines            │
├──────────────────────────────────────────────────────────────────┤
│  DAEMON                                                          │
│  ./ttsc daemon              Start daemon                         │
│  ./ttsc speak "text"        Speak via daemon                     │
│  ./ttsc pause               Pause playback                       │
│  ./ttsc resume              Resume playback                      │
│  ./ttsc stop                Stop playback                        │
│  ./ttsc stop-daemon         Stop daemon                          │
├──────────────────────────────────────────────────────────────────┤
│  CONFIG: ~/.config/tts/config.yaml                               │
│  language: en-us                                                 │
│  speed: normal                                                   │
│  cache_max_size_mb: 500                                          │
│  notifications: true                                             │
│  default_engine: null                                            │
├──────────────────────────────────────────────────────────────────┤
│  FILES                                                           │
│  Config:    ~/.config/tts/config.yaml                            │
│  Cache:     ~/.cache/tts_app/                                    │
│  Debug log: /tmp/tts_debug.log                                   │
│  Wrappers:  ~/.local/bin/tts*                                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## Support

For issues and feature requests, please check the project repository.
