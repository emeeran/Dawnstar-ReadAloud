# 🎛️ Features and Commands Reference

## 🌟 Key Features

### 1. **Intelligent Text Processing**
- **Smart Chunking**: Splits text into 500-character chunks at natural boundaries (sentences, clauses) for smooth playback.
- **Text Cleaning**: Removes URLs, emails, and formatting artifacts.
- **Formats**: Supports `.txt`, `.md`, `.pdf` (via poppler), and URLs.

### 2. **Performance & Caching**
- **Instant Replay**: Audio is cached in `~/.cache/tts_app/` using MD5 hashes.
- **Robustness**: Timeouts for network/PDF operations prevents hanging.
- **Offline Support**: Plays cached content without internet.

### 3. **Desktop Integration**
- **Global Shortcut**: Speak selected text with `Ctrl+Alt+S`.
- **Stdin Support**: Pipe text to TTS via standard input.
- **Automated Setup**: Script included to configure shortcuts.

### 4. **Language Support**
Strictly supports these three variants:
- **`en-us`**: English (United States) [Default]
- **`en-uk`**: English (United Kingdom)
- **`ta`**: Tamil

---

## 🛠️ Command-Line Interface (CLI)

### Modes of Operation

1. **Interactive Mode**: Run `./tts` without arguments to launch a menu system where you can change settings and input text.
2. **CLI Mode**: Run `./tts [SOURCE]` to immediately process a file or URL.

### Syntax
```bash
./tts [SOURCE] [OPTIONS]
```

### Arguments
| Argument | Description |
|----------|-------------|
| `SOURCE` | File path, URL, or `-` for stdin. If omitted, enters interactive mode. |

### Options

#### **Speech Control**
| Flag | Description | Values | Default |
|------|-------------|--------|---------|
| `-l`, `--lang` | Language code | `en-us`, `en-uk`, `ta` | `en-us` |
| `-s`, `--speed` | Speech rate | `slow`, `normal`, `fast` | `normal` |

#### **System & Debug**
| Flag | Description |
|------|-------------|
| `-v`, `--verbose` | Enable command logs, player output, and chunk progress. |
| `--no-cache` | Force re-generation of audio (ignore cache). |
| `--clear-cache` | Delete all cached audio files and exit. |
| `-h`, `--help` | Show help message. |

---

## 💡 Quick Cheat Sheet

| Task | Command |
|------|---------|
| **Read File** | `./tts file.txt` |
| **Read Webpage** | `./tts https://google.com` |
| **Read Selection** | Highlight + `Ctrl+Alt+S` |
| **Slow Speed** | `./tts file.txt --speed slow` |
| **Tamil** | `./tts file.txt --lang ta` |
| **Clear Cache** | `./tts --clear-cache` |
