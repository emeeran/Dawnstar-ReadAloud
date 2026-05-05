"""Runtime support utilities for notifications and cache management."""

import shutil
import subprocess
from pathlib import Path
from typing import Any

from .constants import CACHE_DIR


class NotificationManager:
    """Desktop notification support."""

    _enabled: bool = True
    _available: bool | None = None

    @classmethod
    def is_available(cls) -> bool:
        """Check if notify-send is available."""
        if cls._available is None:
            cls._available = shutil.which("notify-send") is not None
        return cls._available

    @classmethod
    def notify(cls, title: str, message: str, timeout: int = 2000) -> bool:
        """Send a desktop notification."""
        if not cls._enabled or not cls.is_available():
            return False

        try:
            subprocess.run(
                ["notify-send", "-t", str(timeout), title, message],
                capture_output=True,
                timeout=5,
            )
            return True
        except (OSError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return False

    @classmethod
    def set_enabled(cls, enabled: bool) -> None:
        """Enable or disable notifications."""
        cls._enabled = enabled


class CacheManager:
    """LRU cache manager with size limits."""

    _initialized: bool = False
    _max_size_bytes: int = 500 * 1024 * 1024

    @classmethod
    def initialize(cls, max_size_mb: int = 500) -> None:
        """Initialize cache with size limit."""
        if cls._initialized:
            return
        cls._max_size_bytes = max_size_mb * 1024 * 1024
        cls._initialized = True
        cls._enforce_limit()

    @classmethod
    def get_cache_stats(cls) -> dict[str, Any]:
        """Get cache statistics."""
        if not CACHE_DIR.exists():
            return {"files": 0, "size_bytes": 0, "size_mb": 0.0}

        total_size = 0
        file_count = 0
        for file_path in CACHE_DIR.glob("*.mp3"):
            try:
                total_size += file_path.stat().st_size
                file_count += 1
            except OSError:
                pass

        return {
            "files": file_count,
            "size_bytes": total_size,
            "size_mb": round(total_size / (1024 * 1024), 2),
            "max_size_mb": cls._max_size_bytes // (1024 * 1024),
        }

    @classmethod
    def _enforce_limit(cls) -> None:
        """Remove oldest files if cache exceeds size limit."""
        if not CACHE_DIR.exists():
            return

        files: list[tuple[float, Path, int]] = []
        total_size = 0
        for file_path in CACHE_DIR.glob("*.mp3"):
            try:
                stats = file_path.stat()
                files.append((stats.st_mtime, file_path, stats.st_size))
                total_size += stats.st_size
            except OSError:
                pass

        files.sort()
        for _, file_path, size in files:
            if total_size <= cls._max_size_bytes:
                break
            try:
                file_path.unlink()
                total_size -= size
            except OSError:
                pass

    @classmethod
    def clear(cls) -> int:
        """Clear all cache files and return number of deleted files."""
        if not CACHE_DIR.exists():
            return 0

        count = 0
        for file_path in CACHE_DIR.glob("*.mp3"):
            try:
                file_path.unlink()
                count += 1
            except OSError:
                pass
        return count
