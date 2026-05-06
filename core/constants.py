"""Shared constants for TTS application.

This module defines all application-wide constants including:
- Cache and file paths
- Language configurations and aliases
- Speed mappings for different TTS engines
- File suffixes for audio formats
"""

from pathlib import Path

# ANSI escape sequences for highlighting
ANSI_RESET = "\033[0m"
ANSI_GREY_BG = "\033[48;5;238m"  # ~20% grey background
# Cache configuration
CACHE_DIR: Path = Path.home() / ".cache" / "tts_app"
"""Directory for caching generated audio files."""

# Text processing
CHUNK_SIZE: int = 100
"""Maximum characters per text chunk for TTS processing."""

DEFAULT_LANG: str = "en-us"
"""Default language code for TTS synthesis."""

# File extensions
TEMP_FILE_SUFFIX: str = ".mp3"
"""File extension for MP3 audio files."""

WAV_SUFFIX: str = ".wav"
"""File extension for WAV audio files."""

# Language configurations for Edge TTS and gTTS backends
LANG_CONFIG: dict[str, dict[str, str | None]] = {
    "en-us": {
        "name": "English (US)",
        "voice": "en-US-GuyNeural",
        "fallback_tld": "us",
    },
    "en-uk": {
        "name": "English (UK)",
        "voice": "en-GB-RyanNeural",
        "fallback_tld": "co.uk",
    },
    "ta": {
        "name": "Tamil",
        "voice": "ta-IN-ValluvarNeural",
        "fallback_tld": None,
    },
}
"""Language configuration mapping with voice names and gTTS fallback TLDs."""

LANG_ALIASES: dict[str, str] = {"en": "en-us", "en-gb": "en-uk"}
"""Language code aliases for user-friendly input."""

# Speed mappings for Edge TTS
SPEED_MAP: dict[str, str] = {
    "slow": "-25%",
    "normal": "+0%",
    "fast": "+25%",
}
"""Speed adjustment strings for Edge TTS rate parameter."""

# Speed mappings for eSpeak backend
ESPEAK_SPEED_MAP: dict[str, str] = {
    "slow": "120",
    "normal": "160",
    "fast": "200",
}
"""Words per minute settings for eSpeak engine."""

ESPEAK_VOICE_MAP: dict[str, str] = {
    "en-us": "en-us",
    "en-uk": "en-uk",
    "ta": "ta-in",
}
"""Voice identifiers for eSpeak engine."""
