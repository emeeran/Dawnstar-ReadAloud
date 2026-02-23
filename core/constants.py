"""Shared constants for TTS application."""

from pathlib import Path

CACHE_DIR = Path.home() / ".cache" / "tts_app"
CHUNK_SIZE = 500
DEFAULT_LANG = "en-us"
TEMP_FILE_SUFFIX = ".mp3"
WAV_SUFFIX = ".wav"

LANG_CONFIG = {
    "en-us": {"name": "English (US)", "voice": "en-US-GuyNeural", "fallback_tld": "us"},
    "en-uk": {"name": "English (UK)", "voice": "en-GB-RyanNeural", "fallback_tld": "co.uk"},
    "ta": {"name": "Tamil", "voice": "ta-IN-ValluvarNeural", "fallback_tld": None},
}

LANG_ALIASES = {"en": "en-us", "en-gb": "en-uk"}

SPEED_MAP = {"slow": "-25%", "normal": "+0%", "fast": "+25%"}

ESPEAK_SPEED_MAP = {"slow": "120", "normal": "160", "fast": "200"}
ESPEAK_VOICE_MAP = {"en-us": "en-us", "en-uk": "en-uk", "ta": "ta-in"}
