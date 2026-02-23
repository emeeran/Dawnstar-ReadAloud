"""Core TTS components."""

from .constants import CACHE_DIR, LANG_CONFIG
from .config import TTSConfig
from .engine import TTSEngine
from .exceptions import (
    TTSError,
    ConfigurationError,
    ExtractionError,
    EngineError,
    PlaybackError,
    IPCError,
    CacheError,
    SecurityError,
)
from .extractor import ContentExtractor
from .logger import Logger
from .player import AudioPlayer
from .platform import (
    DisplayServer,
    DesktopEnvironment,
    detect_os,
    detect_display_server,
    detect_desktop_environment,
    get_clipboard_text,
    detect_available_engines,
)
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
