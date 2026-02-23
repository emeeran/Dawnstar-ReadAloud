"""Core TTS configuration models.

This module provides the runtime configuration dataclass used throughout
the TTS application for engine settings and behavior control.
"""

from dataclasses import dataclass
from typing import Optional

from .constants import CACHE_DIR, DEFAULT_LANG, LANG_ALIASES, LANG_CONFIG


@dataclass
class TTSConfig:
    """Runtime TTS configuration settings.

    This dataclass holds the configuration for TTS engine operations,
    including language selection, speed control, and caching behavior.

    Attributes:
        lang: Language code (e.g., 'en-us', 'en-uk', 'ta').
        cache_enabled: Whether to cache generated audio files.
        verbose: Whether to output verbose logging information.
        speed: Speech speed ('slow', 'normal', or 'fast').
        engine: Preferred TTS engine (None for auto-selection).

    Example:
        >>> config = TTSConfig(lang='en-us', speed='fast')
        >>> config.lang
        'en-us'
    """

    lang: str = DEFAULT_LANG
    cache_enabled: bool = True
    verbose: bool = False
    speed: str = "normal"
    engine: Optional[str] = None

    def __post_init__(self) -> None:
        """Normalize language code and ensure cache directory exists.

        Language aliases (e.g., 'en' -> 'en-us', 'en-gb' -> 'en-uk')
        are automatically resolved to their canonical forms.
        """
        if self.lang not in LANG_CONFIG:
            self.lang = LANG_ALIASES.get(self.lang, DEFAULT_LANG)
        if self.cache_enabled:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
