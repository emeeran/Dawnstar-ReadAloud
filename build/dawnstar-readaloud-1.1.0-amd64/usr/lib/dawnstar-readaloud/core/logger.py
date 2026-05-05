"""Logging helpers."""

from .config import TTSConfig


class Logger:
    """Simple verbose logger."""

    @staticmethod
    def log(msg: str, config: TTSConfig) -> None:
        """Log message if verbose mode is enabled."""
        if config.verbose:
            print(f"✓ {msg}")

    @staticmethod
    def error(msg: str) -> None:
        """Log error message."""
        print(f"✗ {msg}")
