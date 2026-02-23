#!/usr/bin/env python3
"""Enhanced Text-to-Speech Application entrypoint."""
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


def main() -> int:
    """Application entry point."""
    return CLI().run()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(0)
