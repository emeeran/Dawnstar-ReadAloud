"""Input-source loading and filesystem safety checks."""

import os
import sys
from pathlib import Path
from typing import Optional

from .config import TTSConfig
from .document_readers import extract_epub, extract_pdf
from .url_reader import extract_url_content
from .logger import Logger

__all__ = ["from_source"]


def from_source(source: str, config: TTSConfig) -> Optional[str]:
    """Load text from stdin/file path/URL or return direct text input."""
    if source == "-":
        return sys.stdin.read()

    source = source.strip().strip("'").strip('"')

    # Expand user (~) and environment variables
    expanded_source = os.path.expanduser(os.path.expandvars(source))

    # Check for URL
    if source.startswith(("http://", "https://")):
        Logger.log(f"Fetching URL: {source}", config)
        return extract_url_content(source)

    if os.path.exists(expanded_source):
        try:
            resolved_path = Path(expanded_source).resolve()
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

        source_lower = expanded_source.lower()
        if source_lower.endswith(".epub"):
            return extract_epub(str(resolved_path), config)
        if source_lower.endswith(".pdf"):
            return extract_pdf(str(resolved_path), config)

        try:
            return resolved_path.read_text(encoding="utf-8", errors="ignore")
        except OSError as error:
            Logger.log(f"Read error: {error}", config)
            return None

    # If it looks like a file but doesn't exist, don't treat it as direct text
    file_extensions = ('.txt', '.pdf', '.epub', '.md', '.html', '.htm')
    if source.lower().endswith(file_extensions) or source.startswith(('/', './', '../')):
        Logger.log(f"File not found: {expanded_source}", config)
        return None

    return source
