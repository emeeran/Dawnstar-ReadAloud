"""Content extraction and preprocessing utilities."""


from .config import TTSConfig
from .constants import CHUNK_SIZE
from .document_readers import (
    FRONT_MATTER_PATTERNS,
    extract_epub,
    extract_pdf,
    is_front_matter,
)
from .source_loader import from_source
from .text_processing import chunk_text, clean_text


class ContentExtractor:
    """Extract and process text content from various sources."""

    FRONT_MATTER_PATTERNS = FRONT_MATTER_PATTERNS

    @staticmethod
    def clean_text(text: str) -> str:
        return clean_text(text)

    @staticmethod
    def chunk_text(text: str, size: int = CHUNK_SIZE) -> list[str]:
        return chunk_text(text, size=size)

    @classmethod
    def from_source(cls, source: str, config: TTSConfig) -> str | None:
        return from_source(source, config)

    @staticmethod
    def _is_front_matter(filename: str, title: str = "") -> bool:
        return is_front_matter(filename, title)

    @staticmethod
    def _extract_epub(path: str, config: TTSConfig) -> str | None:
        return extract_epub(path, config)

    @staticmethod
    def _extract_pdf(path: str, config: TTSConfig) -> str | None:
        return extract_pdf(path, config)
