"""Logging helpers."""

import logging

from .config import TTSConfig

# Module-level logger for production use
log = logging.getLogger("tts")


class Logger:
    """Simple verbose logger (backward-compatible facade)."""

    @staticmethod
    def log(msg: str, config: TTSConfig) -> None:
        """Log message if verbose mode is enabled."""
        if config.verbose:
            log.info(msg)

    @staticmethod
    def error(msg: str) -> None:
        """Log error message."""
        log.error(msg)
