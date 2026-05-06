# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Linux Text-to-Speech (TTS) command-line application that reads text from files, PDFs, EPUBs, URLs, or direct input. It features smart caching, multi-language support (US English, UK English, Tamil), and deep system integration including global keyboard shortcuts for reading selected text.

**Core Architecture**: Modular Python application with a `core/` package containing distinct modules for each responsibility. The app uses Edge TTS (Microsoft Azure neural voices) as the primary engine, with gTTS and eSpeak as fallbacks.

## Common Commands

### Development
```bash
# Install dependencies
sudo apt install mpg123 xclip poppler-utils
python3 -m venv .venv
./.venv/bin/pip install -e ".[dev]"

# Run the application
./tts document.txt                    # Read a file
./tts https://example.com/article     # Read a URL
./tts                                 # Interactive mode
./tts -l en-uk -s fast text           # Language and speed options
./tts --clear-cache                   # Clear audio cache

# Run tests
./.venv/bin/python -m pytest tests/ -v

# System integration
python3 configure.py                  # Install keyboard shortcuts and desktop entry
```

### Docker
```bash
docker build -t dawnstar-readaloud .
docker run --rm -i --device /dev/snd dawnstar-readaloud "Hello world"
```

## Architecture

### Project Structure

```
dawnstar-readaloud/
├── app.py              # Main entry point
├── app_config.py       # Application configuration (YAML-based)
├── configure.py        # System integration setup
├── core/               # Core TTS modules
│   ├── __init__.py     # Package exports
│   ├── cli.py          # Command-line interface
│   ├── config.py       # Runtime TTS configuration
│   ├── constants.py    # Application constants
│   ├── engine.py       # TTS backends (Edge, gTTS, eSpeak)
│   ├── exceptions.py   # Custom exception hierarchy
│   ├── extractor.py    # Content extraction facade
│   ├── document_readers.py  # EPUB/PDF extraction
│   ├── source_loader.py     # File/URL loading
│   ├── text_processing.py   # Text cleaning/chunking
│   ├── logger.py       # Verbose logging
│   ├── player.py       # Audio playback
│   ├── platform.py     # Cross-platform detection
│   └── runtime.py      # Cache/Notification managers
├── ttsd/               # Optional daemon for low-latency
│   ├── __init__.py     # Daemon exports
│   ├── daemon.py       # Queue-based TTS daemon
│   └── ipc.py          # Unix socket IPC
└── tests/              # Test suite
```

### Main Components (core/)

The application is organized into distinct modules, each with a single responsibility:

1. **`core/config.py`** - `TTSConfig` dataclass: Runtime configuration for language, speed, caching, verbosity. Normalizes language aliases (e.g., `en` → `en-us`).

2. **`core/extractor.py`** - `ContentExtractor` facade: Handles all input sources and text processing.

3. **`core/engine.py`** - `TTSEngine` with pluggable backends:
   - `EdgeTTSBackend`: Azure neural voices (primary)
   - `GTTSBackend`: Google TTS (fallback)
   - `EspeakBackend`: Local eSpeak (last resort)
   - MD5-based caching in `~/.cache/tts_app/`

4. **`core/player.py`** - `AudioPlayer`: Auto-detects and plays audio (mpg123 → paplay → cvlc → ffplay).

5. **`core/platform.py`** - Cross-platform detection for display server, desktop environment, and clipboard.

6. **`core/exceptions.py`** - Custom exception hierarchy: `TTSError`, `EngineError`, `PlaybackError`, etc.

### Data Flow
```
Input Source → ContentExtractor → Text Cleaning → Chunking →
TTSEngine (with caching) → AudioPlayer → System Sound
```

### Language Configuration

Languages are defined in `core/constants.py` `LANG_CONFIG`. Each language maps to an Edge TTS voice and a gTTS fallback TLD. To add a language, add an entry there.

### System Integration (configure.py)

The `configure.py` script sets up:
- Desktop environment keyboard shortcuts (Ctrl+Alt+S for speak, Ctrl+Alt+Q for stop)
- Desktop entry in `~/.local/share/applications/`
- Wrapper scripts in `~/.local/bin/`

## Key Implementation Details

- **Chunking**: Text is split at sentence boundaries (`. ! ?`) to maintain natural speech rhythm
- **Cache Key**: `md5(text + lang + speed)` ensures different settings generate different audio
- **Clipboard Priority**: On X11, primary selection (highlighted text) is prioritized over clipboard (Ctrl+C)
- **EPUB Processing**: Skips front matter (TOC, preface, copyright) based on filename/title heuristics
- **Language Mapping**: Supports aliases like `en` → `en-us`, `en-gb` → `en-uk`

## Dependencies

**Python**: `edge-tts>=6.1.9`, `gtts>=2.5.4`, `ebooklib>=0.18`, `beautifulsoup4>=4.12.0`, `pyyaml>=6.0`, `pyperclip>=1.8.2`, `pypdf>=6.7.1`

**System**: `mpg123` (recommended), `xclip` or `wl-clipboard` (for keyboard shortcuts), `poppler-utils` (PDF support)

# Project Rules & Guidelines

## 1. Persona & Behavior
* **Role:** You are a Senior Principal Full-Stack Engineer and Architect.
* **Tone:** Concise, authoritative, and helpful. Avoid fluff.
* **Philosophy:** Follow the **3C Protocol**:
    * **Compress:** Write concise, efficient code.
    * **Compile:** Ensure code is executable and logically sound before outputting.
    * **Consolidate:** specific logic goes into utility functions; do not repeat code (DRY).
* **Response Style:**
    * When planning: Use "Deep Think" mode to outline architecture.
    * When coding: Output the full file content unless the change is trivial (one-liner).
    * No "placeholders" or "todo" comments unless explicitly asked.

## 2. Context Detection
* **IF** editing files in `/backend` or ending in `.py` -> Apply **PYTHON RULES**.
* **IF** editing files in `/frontend` or ending in `.js/.jsx/.ts/.tsx` -> Apply **JAVASCRIPT RULES**.
* **IF** editing files in `/scripts` or `.sh` -> Apply **DEVOPS RULES**.

---

## 3. PYTHON RULES (Backend/AI)
* **Version:** Python 3.12+
* **Style:** Follow PEP 8 strict.
* **Typing:**
    * **MUST** use static typing for all function signatures (arguments and return types).
    * Use `typing.Optional`, `typing.List`, or standard generic collections.
    * Use `Pydantic` models for all data schemas and API responses.
* **Error Handling:**
    * No bare `try/except` blocks. Catch specific exceptions.
    * Use custom exception classes for domain-specific errors.
* **Documentation:**
    * Google-style docstrings for all classes and public functions.
* **AI/CLI Tools:**
    * When building CLI tools, use `Typer` or `Click`.
    * Isolate API keys (Gemini, OpenAI) in `os.environ`. Never hardcode keys.

## 4. JAVASCRIPT/TYPESCRIPT RULES (Frontend)
* **Framework:** React / Next.js (App Router).
* **Style:** Functional components only. No class components.
* **State Management:**
    * Use `useState` for local state.
    * Use `Context` or `Zustand` for global state. Avoid Redux boilerplate.
* **Styling:**
    * Use Tailwind CSS. Avoid raw CSS files where possible.
    * Use descriptive class names if custom CSS is required.
* **Async:**
    * Always use `async/await`. Avoid `.then()` chains.
    * Wrap API calls in standard error handling hooks.

## 5. DEVOPS & INFRASTRUCTURE
* **Environment:**
    * Respect `.env` files.
    * Assume Linux (Ubuntu) environment for shell commands.
* **Docker:**
    * Keep images lightweight (use `python:slim` or `node:alpine`).
    * Multi-stage builds are required for production Dockerfiles.

## 6. GIT & VERSION CONTROL
* **Commit Messages:** Conventional Commits format (e.g., `feat: add user login`, `fix: resolve jwt timeout`).
* **Sensitivity:** NEVER output `.env` files, API keys, or passwords in git commits or chat logs.

---

## 7. CRITICAL INSTRUCTIONS
* If a request is ambiguous, ask **one** clarifying question before generating code.
* Always favor **Modern** syntax over legacy (e.g., f-strings over `.format()`, Arrow functions over `function`).
* When editing a file, ensure imports are optimized and unused imports are removed.
