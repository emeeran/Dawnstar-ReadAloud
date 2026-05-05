"""Input-source loading and filesystem safety checks."""

import os
import sys
from pathlib import Path

from .config import TTSConfig
from .document_readers import extract_epub, extract_pdf
from .exceptions import SecurityError
from .logger import Logger
from .url_reader import extract_url_content

__all__ = ["from_source"]


# Maximum size for plain text files (10 MB) to prevent OOM
_MAX_TEXT_FILE_SIZE = 10 * 1024 * 1024


def from_source(source: str, config: TTSConfig) -> str | None:
    """Load text from stdin/file path/URL or return direct text input."""
    if source == "-":
        return sys.stdin.read()

    source = source.strip().strip("'").strip('"')

    # Expand user home (~) only — not env vars, to prevent injection
    expanded_source = os.path.expanduser(source)

    # Check for URL
    if source.startswith(("http://", "https://")):
        Logger.log(f"Fetching URL: {source}", config)
        return extract_url_content(source)

    # Resolve and validate file path
    try:
        resolved_path = Path(expanded_source).resolve()
    except (OSError, ValueError) as error:
        # Not a valid path — treat as direct text input
        return source

    # SECURITY: Validate resolved path is within allowed directories
    allowed_prefixes = [Path.home(), Path("/tmp"), Path("/var/tmp")]
    is_allowed = any(
        resolved_path == prefix or resolved_path.is_relative_to(prefix)
        for prefix in allowed_prefixes
    )

    if not is_allowed:
        Logger.log("Access denied: path outside allowed directories", config)
        raise SecurityError("Access denied: path outside allowed directories")

    source_lower = expanded_source.lower()
    if source_lower.endswith(".epub"):
        return extract_epub(str(resolved_path), config)
    if source_lower.endswith(".pdf"):
        return extract_pdf(str(resolved_path), config)

    # Read plain text file with size limit
    try:
        file_size = resolved_path.stat().st_size
        if file_size > _MAX_TEXT_FILE_SIZE:
            Logger.log(
                f"File too large ({file_size // (1024 * 1024)} MB, max 10 MB)", config
            )
            return None
        return resolved_path.read_text(encoding="utf-8", errors="ignore")
    except OSError as error:
        # File doesn't exist or unreadable
        file_extensions = ('.txt', '.pdf', '.epub', '.md', '.html', '.htm')
        if source.lower().endswith(file_extensions) or source.startswith(('/', './', '../')):
            Logger.log(f"File not found: {expanded_source}", config)
            return None
        # Not a file path — treat as direct text input
        return source
