# Build a Linux TTS System with Neural Voices in 5 Minutes

*Transform your Linux desktop into a text-to-speech powerhouse with natural-sounding AI voices*

---

## Why I Built This

I wanted my computer to read articles aloud while I cook. The existing options were either robotic (espeak), paid services, or required cloud accounts. So I built a lightweight TTS tool using Microsoft's free Edge neural voices.

The result: A 500-line Python app that speaks naturally, caches audio for instant replay, and integrates with global keyboard shortcuts.

## Quick Start

```bash
# Install dependencies
sudo apt install mpg123 xclip
git clone <repo-url> tts && cd tts
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# Test it
./tts "Hello! This sounds surprisingly natural."
```

## The Cool Parts

### 1. Neural Voices, Offline Cache

First playback hits Edge TTS API (~1s), but subsequent plays are instant thanks to MD5-based caching:

```bash
./tts "First time"     # ~1 second (network)
./tts "First time"     # Instant (cached)
```

### 2. Global Keyboard Shortcuts

Highlight text anywhere, press `Ctrl+Alt+S`, listen:

```bash
python3 configure.py  # Auto-detects GNOME/KDE/XFCE/Sway
```

### 3. E-books on Autopilot

```bash
./tts my_novel.epub   # Reads entire EPUB
```

### 4. Pipe Anything

```bash
# Read terminal output
git log -1 --pretty=%B | ./tts -

# Morning briefing
./tts "$(date +'Today is %A, %B %d')"
```

### 5. Optional Daemon Mode

For frequent use, the daemon cuts latency from 500ms to 50ms:

```bash
./ttsc daemon --fork   # Background
./ttsc speak "Fast!"
./ttsc stop-daemon
```

## Useful Scripts

### Daily News Briefing

```bash
#!/bin/bash
# ~/bin/morning-briefing

./tts "Good morning. Here's your briefing for $(date +'%A, %B %d')."
./tts "You have $(cal | grep -c $(date +%-d)) events today."
```

### Git Commit Announcer

```bash
#!/bin/bash
# Add to .git/hooks/post-commit

./tts "Commit $(git rev-parse --short HEAD) pushed."
```

### Read Selection (Enhanced)

```bash
#!/bin/bash
# Speak selection with notification

TEXT=$(xclip -o -selection primary 2>/dev/null || xclip -o -selection clipboard)
if [ -n "$TEXT" ]; then
    notify-send "TTS" "Speaking ${#TEXT} characters..."
    ./tts "$TEXT"
fi
```

### Speed Reading Helper

```bash
#!/bin/bash
# Read clipboard at 2x speed for speed-reading practice

./tts --speed fast "$(xclip -o -selection clipboard)"
```

### Proofreading Script

```bash
#!/bin/bash
# Read file slowly for proofreading

if [ -z "$1" ]; then
    echo "Usage: $0 <file>"
    exit 1
fi

./tts --speed slow --lang en-uk "$1"
```

## Configuration

Save preferences in `~/.config/tts/config.yaml`:

```yaml
language: en-us
speed: normal
cache_max_size_mb: 500
notifications: true
progress: true
```

## The Stack

- **Edge TTS**: Microsoft Azure neural voices (free)
- **gTTS**: Google TTS fallback
- **mpg123**: Audio playback
- **xclip/wl-paste**: Clipboard access

## Try It

```bash
# One-liner demo
curl -s https://example.com/article | ./tts -
```

The full source is available with configuration, daemon mode, EPUB support, and more. Happy listening!

---

*Built with Python 3.12, works on Ubuntu/Debian. Supports GNOME, KDE, XFCE, Sway, and Hyprland.*
