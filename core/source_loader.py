"""Input-source loading and filesystem safety checks."""

import os
import sys
from pathlib import Path
from typing import Optional

from .config import TTSConfig
from .document_readers import extract_epub, extract_pdf
from .logger import Logger

__all__ = ["from_source"]


def from_source(source: str, config: TTSConfig) -> Optional[str]:
    """Load text from stdin/file path or return direct text input."""
    if source == "-":
        return sys.stdin.read()

    source = source.strip().strip("'").strip('"')

    if os.path.exists(source):
        try:
            resolved_path = Path(source).resolve()
        except (OSError, ValueError) as error:
            Logger.log(f"Invalid path: {error}", config)
            return None

        home = Path.home()
        allowed_prefixes = [home, Path("/tmp"), Path("/var/tmp")]
        is_allowed = any(str(resolved_path).startswith(str(prefix)) for prefix in allowed_prefixes)
        if not is_allowed and not source.startswith("/"):
            is_allowed = True

        if not is_allowed:
            Logger.log("Access denied: path outside allowed directories", config)
            return None

        source_lower = source.lower()
        if source_lower.endswith(".epub"):
            return extract_epub(str(resolved_path), config)
        if source_lower.endswith(".pdf"):
            return extract_pdf(str(resolved_path), config)

        try:
            return resolved_path.read_text(encoding="utf-8", errors="ignore")
        except OSError as error:
            Logger.log(f"Read error: {error}", config)
            return None

    return source
