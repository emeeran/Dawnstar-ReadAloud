# 📘 TTS Application - Comprehensive Documentation

This generic guide covers installation, system integration, troubleshooting, and advanced usage patterns for the Enhanced TTS Application.

---

## 📋 Table of Contents
1. [Installation Guide](#1-installation-guide)
2. [System Integration (Global Keyboard Shortcut)](#2-system-integration-global-keyboard-shortcut)
3. [Troubleshooting](#3-troubleshooting)
4. [Advanced Usage Examples](#4-advanced-usage-examples)

---

## 1. Installation Guide

### Quick Install (Ubuntu/Debian)

```bash
# 1. Install system dependencies (mpg123 is recommended for best audio)
sudo apt update && sudo apt install -y mpg123 xclip

# 2. Create virtual environment
python3 -m venv venv

# 3. Install Python dependencies
./venv/bin/pip install -r requirements.txt

# 4. Make launcher executable
chmod +x tts

# 5. Verify installation
./tts quick_test.txt -v
```

### Supported Platforms & Dependencies

| Platform | Recommended Player | Install Command |
|----------|--------------------|-----------------|
| **Linux** | `mpg123` | `sudo apt install mpg123` |
| **macOS** | `mpg123` | `brew install mpg123` |

**Optional Dependencies:**
- `poppler-utils`: For PDF reading support.
- `lynx`: For better web page text extraction.

---

## 2. System Integration (Global Keyboard Shortcut)

You can configure a global hotkey (e.g., `Ctrl+Alt+S`) to read any text you highlight on your screen.

### 🚀 Automated Setup (Recommended)
Run the included setup script to automatically register the shortcut:

```bash
python3 setup_shortcut.py
```

### ⚙️ Manual Setup
If the automated script fails, follow these steps:

1. Open **Settings** > **Keyboard** > **Shortcuts** > **Custom Shortcuts**.
2. Click **Add Shortcut**.
3. **Name**: Speak Selection
4. **Command**: `/path/to/tts/speak_selection.sh`
   *(Run `pwd` in the tts folder to get the full path)*
5. **Shortcut**: Press `Ctrl+Alt+S` (or your preferred key).

### 🎮 How to Use
1. Highlight text in any application (Browser, Editor, PDF).
2. Press **Ctrl+Alt+S**.
3. The computer will read the text aloud!

---

## 3. Troubleshooting

### No Audio Output 🔇
If the app runs but remains silent:
1. **Install mpg123**: VLC can have issues in headless mode. `sudo apt install mpg123`.
2. **Check System Audio**: Run `writer-test` or play a YouTube video.
3. **Clear Cache**: Old cached files might be corrupt. `./tts --clear-cache`.

### "xclip not found" Error 📋
The system integration requires `xclip` to grab highlighted text.
- **Fix**: `sudo apt install xclip`

### Language Warnings ⚠️
If you see "Warning: 'fr' is not in the supported list":
- The app restricts languages to **US English**, **British English**, and **Tamil**.
- Use `--lang en-us`, `--lang en-uk`, or `--lang ta`.

---

## 4. Advanced Usage Examples

### 📄 Reading Documents
```bash
# Read a text file with verbose output
./tts meeting_notes.txt -v

# Read a PDF document (requires poppler-utils)
./tts research_paper.pdf

# Read a file with spaces in the name
./tts my daily report.txt
```

### 🌐 Reading Web Content
```bash
# Read a news article directly from URL
./tts https://example.com/breaking-news
```

### 🗣️ Language & Speed Control
```bash
# Tamil Language
./tts tamil_story.txt --lang ta

# British English at slow speed (great for proofreading)
./tts draft.txt --lang en-uk --speed slow
```

### 🛠️ Maintenance
```bash
# Clear the audio cache to free up disk space
./tts --clear-cache

# Force regeneration of audio (ignore existing cache)
./tts script.txt --no-cache
```

### ⚡ Batch Processing
You can pipe text directly into the application:
```bash
echo "System check complete" | ./tts -
```
