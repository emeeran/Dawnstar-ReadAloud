# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Linux Text-to-Speech (TTS) command-line application that reads text from files, PDFs, URLs, or direct input. It features smart caching, multi-language support (US English, UK English, Tamil), and deep system integration including global keyboard shortcuts for reading selected text.

**Core Architecture**: Single-file Python application (`app.py`) with modular classes. The app uses Edge TTS (Microsoft Azure neural voices) as the primary engine, with gTTS as fallback.

## Common Commands

### Development
```bash
# Install dependencies
sudo apt install mpg123 xclip poppler-utils
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# Run the application
./tts document.txt                    # Read a file
./tts https://example.com/article     # Read a URL
./tts                                 # Interactive mode
./tts -l en-uk -s fast text           # Language and speed options
./tts --clear-cache                   # Clear audio cache

# System integration
python3 configure.py                  # Install keyboard shortcuts and desktop entry
```

### Docker
```bash
docker build -t enhanced-tts .
docker run --rm -i --device /dev/snd enhanced-tts "Hello world"
```

## Architecture

### Main Components (app.py)

The application is organized into distinct classes, each with a single responsibility:

1. **`TTSConfig`** (dataclass): Configuration holder - language, speed, caching, verbosity. Normalizes language aliases (e.g., `en` → `en-us`).

2. **`ContentExtractor`**: Handles all input sources and text processing:
   - Input sources: files, URLs, PDFs, stdin (`-`), direct text
   - `clean_text()`: Removes URLs, emails, normalizes whitespace
   - `chunk_text()`: Splits text at sentence boundaries (500 char chunks) for better TTS
   - `from_url()`: HTML parsing with script/style/nav filtering, plus lynx/curl/wget fallback
   - `from_pdf()`: Uses pdftotext, removes TOC and header lines
   - `_clean_content()`: Removes front-matter junk (TOC entries, copyright, ISBN)

3. **`TTSEngine`**: Speech generation with dual-engine fallback:
   - Primary: Edge TTS (Azure neural voices via `edge-tts` binary)
   - Fallback: gTTS (Google TTS, lazily imported)
   - Caching: MD5-based cache in `~/.cache/tts_app/` using `text + lang + speed` as key
   - Auto-detects edge-tts binary in venv (`sys.executable` parent directory)

4. **`AudioPlayer`**: Auto-detects and plays audio through available players:
   - Priority: mpg123 → cvlc → ffplay
   - Uses temporary files for playback

5. **`Logger`**: Verbose logging with emoji prefixes (✓ info, ✗ error)

### Data Flow
```
Input Source → ContentExtractor → Text Cleaning → Chunking →
TTSEngine (with caching) → AudioPlayer → System Sound
```

### Language Configuration

Languages are defined in `LANG_CONFIG` (app.py:29-33). Each language maps to an Edge TTS voice and a gTTS fallback TLD. To add a language, add an entry here with the voice name and fallback TLD.

### System Integration (configure.py)

The `configure.py` script sets up:
- GNOME keyboard shortcuts via gsettings (Ctrl+Alt+S for speak, Ctrl+Alt+Q for stop)
- Desktop entry in `~/.local/share/applications/`
- Installs wrapper scripts to `~/.local/bin/`

The script preserves custom0 (reserved for Flameshot) and uses custom1 and custom2.

## Key Implementation Details

- **Chunking**: Text is split at sentence boundaries (`. ! ? ; : , space`) to maintain natural speech rhythm
- **Cache Key**: `md5(text + lang + speed)` ensures different settings generate different audio
- **Edge TTS Binary Detection**: Checks `Path(sys.executable).parent / 'edge-tts'` for venv-installed binary
- **PDF TOC Removal**: Filters lines ending in dots+numbers and standalone Roman numerals
- **HTML Parsing**: Custom HTMLParser class skips script/style/nav/header/footer/aside tags
- **Language Mapping**: Supports aliases like `en` → `en-us`, `en-gb` → `en-uk`

## Dependencies

**Python**: `edge-tts>=6.1.9`, `gtts==2.5.4`

**System**: `mpg123` (recommended), `xclip` (for keyboard shortcuts), `poppler-utils` (PDF support), `lynx` (web fallback)

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
