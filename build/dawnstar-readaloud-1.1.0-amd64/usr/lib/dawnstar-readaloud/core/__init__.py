"""Core TTS components."""

from .config import TTSConfig
from .constants import CACHE_DIR, LANG_CONFIG
from .engine import TTSEngine
from .exceptions import (
    CacheError,
    ConfigurationError,
    EngineError,
    ExtractionError,
    IPCError,
    PlaybackError,
    SecurityError,
    TTSError,
)
from .extractor import ContentExtractor
from .logger import Logger
from .platform import (
    DesktopEnvironment,
    DisplayServer,
    detect_available_engines,
    detect_desktop_environment,
    detect_display_server,
    detect_os,
    get_clipboard_text,
)
from .player import AudioPlayer
from .runtime import CacheManager, NotificationManager

__all__ = [
    # Constants
    "CACHE_DIR",
    "LANG_CONFIG",
    # Configuration
    "TTSConfig",
    # Engine
    "TTSEngine",
    # Exceptions
    "TTSError",
    "ConfigurationError",
    "ExtractionError",
    "EngineError",
    "PlaybackError",
    "IPCError",
    "CacheError",
    "SecurityError",
    # Extraction
    "ContentExtractor",
    # Platform detection
    "DisplayServer",
    "DesktopEnvironment",
    "detect_os",
    "detect_display_server",
    "detect_desktop_environment",
    "get_clipboard_text",
    "detect_available_engines",
    # Utilities
    "Logger",
    "AudioPlayer",
    "CacheManager",
    "NotificationManager",
]
