"""Core TTS configuration models."""

from dataclasses import dataclass
from typing import Optional

from .constants import CACHE_DIR, DEFAULT_LANG, LANG_ALIASES, LANG_CONFIG


@dataclass
class TTSConfig:
    """TTS configuration settings."""

    lang: str = DEFAULT_LANG
    cache_enabled: bool = True
    verbose: bool = False
    speed: str = "normal"
    engine: Optional[str] = None

    def __post_init__(self) -> None:
        """Normalize language code and ensure cache directory exists."""
        if self.lang not in LANG_CONFIG:
            self.lang = LANG_ALIASES.get(self.lang, DEFAULT_LANG)
        if self.cache_enabled:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
