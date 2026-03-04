"""TTS application entry point.

This module serves as the main entry point and re-exports core components
for external use and testing.
"""

import contextlib
import sys

from core import (
    CACHE_DIR,
    CacheManager,
    ContentExtractor,
    NotificationManager,
    TTSConfig,
    TTSEngine,
)
from core.cli import CLI
from core.constants import CHUNK_SIZE, LANG_CONFIG, SPEED_MAP

__all__ = [
    # From core
    "CACHE_DIR",
    "CacheManager",
    "ContentExtractor",
    "NotificationManager",
    "TTSConfig",
    "TTSEngine",
    # From core.constants
    "CHUNK_SIZE",
    "LANG_CONFIG",
    "SPEED_MAP",
    # CLI
    "CLI",
]


def main() -> int:
    """Application entry point."""
    return CLI().run()


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        sys.exit(main())
