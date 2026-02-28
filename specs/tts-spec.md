# TTS Application Specification

Version: 1.0.0
Last Updated: 2026-02-28

## Overview

A Linux Text-to-Speech (TTS) command-line application that reads text from files, PDFs, EPUBs, URLs, or direct input. Features smart caching, multi-language support (US English, UK English, Tamil), and deep system integration including global keyboard shortcuts.

---

## Table of Contents

1. [Text-to-Speech Engine](#1-text-to-speech-engine)
2. [Content Extraction](#2-content-extraction)
3. [Text Processing](#3-text-processing)
4. [Audio Caching](#4-audio-caching)
5. [Audio Playback](#5-audio-playback)
6. [CLI Interface](#6-cli-interface)
7. [Platform Detection](#7-platform-detection)
8. [Daemon Mode](#8-daemon-mode)

---

## 1. Text-to-Speech Engine

### 1.1 Multi-Backend Architecture

**Requirement**: The system shall support multiple TTS backends with automatic fallback.

**Backends (in priority order)**:
1. **Edge TTS** - Microsoft Azure neural voices (primary)
2. **gTTS** - Google Text-to-Speech (fallback)
3. **eSpeak** - Local synthesis (last resort)

**Acceptance Criteria**:
- [ ] Engine attempts backends in priority order
- [ ] System falls back to next backend on failure
- [ ] Each backend can be queried for availability
- [ ] Backend selection is logged in verbose mode

### 1.2 Language Support

**Requirement**: The system shall support multiple languages with configurable voices.

**Supported Languages**:
| Code | Language | Voice |
|------|----------|-------|
| `en-us` | US English | en-US-AvaNeural |
| `en-uk` | UK English | en-GB-SoniaNeural |
| `ta` | Tamil | ta-IN-PallaviNeural |

**Acceptance Criteria**:
- [ ] Each language maps to correct Edge TTS voice
- [ ] Language aliases are normalized (e.g., `en` -> `en-us`)
- [ ] Invalid language codes raise appropriate error

### 1.3 Speech Rate Control

**Requirement**: The system shall support adjustable speech rates.

**Speed Options**:
| Speed | Edge TTS Rate | gTTS | eSpeak |
|-------|---------------|------|--------|
| `slow` | `-25%` | slow=True | 120 wpm |
| `normal` | `+0%` | slow=False | 175 wpm |
| `fast` | `+50%` | slow=False | 250 wpm |

**Acceptance Criteria**:
- [ ] Speed setting affects audio generation
- [ ] Speed is configurable via CLI flag `-s`
- [ ] Default speed is `normal`

---

## 2. Content Extraction

### 2.1 Direct Text Input

**Requirement**: The system shall accept direct text input from command line.

**Acceptance Criteria**:
- [ ] Text provided as arguments is spoken directly
- [ ] Multiple arguments are concatenated with spaces
- [ ] Empty/whitespace-only input is handled gracefully

### 2.2 File Input

**Requirement**: The system shall read text from various file formats.

**Supported Formats**:
- Plain text files (`.txt`)
- PDF documents (`.pdf`)
- EPUB books (`.epub`)

**Acceptance Criteria**:
- [ ] Text files are read directly
- [ ] PDF files use pypdf library
- [ ] EPUB files use ebooklib library
- [ ] Missing files raise appropriate error
- [ ] Binary files (PDF/EPUB) require appropriate dependencies

### 2.3 URL Input

**Requirement**: The system shall fetch and extract content from web URLs.

**Acceptance Criteria**:
- [ ] HTTP/HTTPS URLs are fetched with appropriate User-Agent
- [ ] HTML is parsed to extract main content
- [ ] Navigation, ads, and sidebars are removed
- [ ] Network errors are handled gracefully
- [ ] URL fetch timeout is configurable (default 20s)

### 2.4 Clipboard Input

**Requirement**: The system shall read text from system clipboard.

**Acceptance Criteria**:
- [ ] X11 primary selection (highlighted text) is prioritized
- [ ] Wayland clipboard is supported
- [ ] Falls back to Ctrl+C clipboard on X11
- [ ] Empty clipboard is handled gracefully

### 2.5 PDF Processing

**Requirement**: The system shall extract main content from PDF documents.

**Features**:
- Skip front matter (preface, TOC, copyright)
- Skip page numbers and headers/footers
- Fix common PDF artifacts (spaced letters, punctuation spacing)
- Start from first detected chapter

**Acceptance Criteria**:
- [ ] Front matter is detected and skipped
- [ ] Page numbers are removed
- [ ] Text artifacts are cleaned
- [ ] Chapter detection identifies content start

### 2.6 EPUB Processing

**Requirement**: The system shall extract main content from EPUB books.

**Features**:
- Skip front matter (TOC, preface, copyright, dedication, etc.)
- Skip back matter (index, bibliography, appendix, glossary)
- Process HTML content from EPUB items

**Acceptance Criteria**:
- [ ] Front/back matter is detected and skipped
- [ ] Only document items are processed
- [ ] HTML is converted to plain text
- [ ] Skipped sections are logged in verbose mode

---

## 3. Text Processing

### 3.1 Text Cleaning

**Requirement**: The system shall clean and normalize input text.

**Cleaning Operations**:
- Remove URLs (http/https)
- Remove email addresses
- Replace non-breaking spaces with regular spaces
- Normalize smart quotes to straight quotes
- Normalize em/en-dashes to hyphens with spaces
- Collapse multiple whitespace to single space

**Acceptance Criteria**:
- [ ] URLs are removed from text
- [ ] Emails are removed from text
- [ ] Whitespace is normalized
- [ ] Smart quotes are converted

### 3.2 Text Chunking
**Requirement**: The system shall split text into speakable chunks.

**Chunking Strategy**:
- Split at sentence boundaries (`.`, `!`, `?`)
- Respect sentence integrity when possible
- Fall back to fixed-size chunks for long sentences
- Maximum chunk size is configurable (default ~200 chars)

**Acceptance Criteria**:
- [ ] Text is split at sentence boundaries
- [ ] Sentences are kept intact when possible
- [ ] Very long sentences are split at chunk size
- [ ] Empty chunks are not produced

---

## 4. Audio Caching

### 4.1 Cache Architecture

**Requirement**: The system shall cache generated audio for instant replay.

**Cache Location**: `~/.cache/tts_app/`

**Cache Key Generation**:
```
key = MD5(text + language + speed)
```

**Acceptance Criteria**:
- [ ] Audio is cached with MD5 key
- [ ] Cache directory is created on first use
- [ ] Cache hit avoids API calls
- [ ] Cache miss triggers generation

### 4.2 Cache Management

**Requirement**: The system shall manage cache size and limits.

**Features**:
- LRU eviction when max size exceeded
- Manual cache clearing via `--clear-cache`
- Cache statistics via `--cache-stats`
- Cache can be disabled via `--no-cache`

**Acceptance Criteria**:
- [ ] Max cache size is configurable
- [ ] Old files are evicted when limit exceeded
- [ ] Cache statistics show file count and size
- [ ] Cache clearing removes all cached files

---

## 5. Audio Playback

### 5.1 Player Detection

**Requirement**: The system shall auto-detect available audio players.

**Player Priority**:
1. `mpg123` - Recommended, supports stdin
2. `paplay` - PulseAudio
3. `cvlc` - VLC media player
4. `ffplay` - FFmpeg

**Acceptance Criteria**:
- [ ] Players are tried in priority order
- [ ] First available player is used
- [ ] Missing player shows actionable error message
- [ ] mpg123 is preferred for stdin support

### 5.2 Playback Execution

**Requirement**: The system shall play audio with proper error handling.

**Acceptance Criteria**:
- [ ] Audio is played to completion
- [ ] Playback errors are caught and reported
- [ ] Timeout prevents hanging (5 minute max)
- [ ] Temporary files are cleaned up after playback

---

## 6. CLI Interface

### 6.1 Command-Line Arguments

**Requirement**: The system shall provide comprehensive CLI options.

**Arguments**:
| Argument | Description |
|----------|-------------|
| `source` | Text, file path, or URL to read (positional) |
| `-l, --lang` | Language code (en-us, en-uk, ta) |
| `-s, --speed` | Speech speed (slow, normal, fast) |
| `-v, --verbose` | Enable verbose output |
| `--no-cache` | Disable audio caching |
| `--clear-cache` | Clear audio cache |
| `--cache-stats` | Show cache statistics |
| `--list-engines` | List available TTS engines |
| `--get-clipboard` | Print clipboard text |
| `--show-config` | Show current configuration |
| `--config-path` | Show config file path |
| `--sentence-file` | Write current sentence to file |

**Acceptance Criteria**:
- [ ] All arguments are parsed correctly
- [ ] Help text is displayed with `--help`
- [ ] Invalid arguments show appropriate error
- [ ] Exit codes: 0 (success), 1 (error)

### 6.2 Interactive Mode

**Requirement**: The system shall support interactive text input.

**Acceptance Criteria**:
- [ ] No arguments starts interactive mode
- [ ] Text is read line by line
- [ ] `quit` exits interactive mode
- [ ] EOF (Ctrl+D) exits gracefully

### 6.3 Progress Indication

**Requirement**: The system shall show progress during speech.

**Acceptance Criteria**:
- [ ] Current sentence is highlighted during speech
- [ ] Progress is shown for multi-chunk text
- [ ] Notifications show start/complete for long text

---

## 7. Platform Detection

### 7.1 Display Server Detection

**Requirement**: The system shall detect the display server type.

**Supported Servers**:
- X11
- Wayland
- macOS Quartz
- Windows

**Acceptance Criteria**:
- [ ] X11 is detected via environment variables
- [ ] Wayland is detected via XDG_SESSION_TYPE
- [ ] macOS/Windows are detected via platform

### 7.2 Clipboard Handling

**Requirement**: The system shall read from the appropriate clipboard.

**X11 Priority**:
1. Primary selection (highlighted text)
2. Clipboard (Ctrl+C)

**Wayland**: Uses `wl-paste` or `wl-clipboard`

**Acceptance Criteria**:
- [ ] X11 primary selection is tried first
- [ ] Falls back to clipboard selection
- [ ] Wayland clipboard is supported
- [ ] Empty clipboard returns empty string

### 7.3 Desktop Environment

**Requirement**: The system shall detect the desktop environment.

**Supported Environments**:
- GNOME
- KDE
- Xfce
- Sway
- Hyprland

**Acceptance Criteria**:
- [ ] Environment is detected via environment variables
- [ ] Unknown environments are handled gracefully
- [ ] Detection is used for notification support

---

## 8. Daemon Mode

### 8.1 Daemon Architecture

**Requirement**: The system shall support a background daemon for low-latency synthesis.

**Features**:
- Unix socket IPC
- Job queue with priorities
- Pause/Resume/Stop controls
- Progress callbacks
- State management (idle/playing/paused)

**Acceptance Criteria**:
- [ ] Daemon starts and listens on socket
- [ ] Multiple jobs are queued
- [ ] Playback controls work correctly
- [ ] State transitions are tracked

### 8.2 IPC Protocol

**Requirement**: The daemon shall communicate via Unix sockets.

**Socket Path**: `$XDG_RUNTIME_DIR/tts-daemon.sock`

**Commands**:
- `speak` - Queue text for synthesis
- `stop` - Stop current playback
- `pause` - Pause playback
- `resume` - Resume playback
- `status` - Get daemon status
- `shutdown` - Stop daemon

**Acceptance Criteria**:
- [ ] Socket is created at standard location
- [ ] Commands are serialized as JSON
- [ ] Responses are JSON with status
- [ ] Socket is cleaned up on shutdown

---

## Cross-Cutting Concerns

- **Security**: File paths are validated to prevent directory traversal
- **Error Handling**: Specific exceptions for each error type
- **Logging**: Verbose mode shows detailed operation info
- **Configuration**: YAML-based with sensible defaults
