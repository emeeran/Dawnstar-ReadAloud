"""Text cleaning and chunking helpers."""

import re

from .constants import CHUNK_SIZE

__all__ = ["clean_text", "chunk_text"]

_RE_URL = re.compile(r"http[s]?://\S+")
_RE_EMAIL = re.compile(r"\S+@\S+")
_RE_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def clean_text(text: str) -> str:
    """Remove URLs/emails and normalize edge whitespace."""
    text = _RE_URL.sub("", text)
    text = _RE_EMAIL.sub("", text)
    return text.strip()


def chunk_text(text: str, size: int = CHUNK_SIZE) -> list[str]:
    """Split text into near-sentence chunks with max size cap."""
    cleaned = text.strip()
    if not cleaned:
        return []
    if len(cleaned) <= size:
        return [cleaned]

    sentences = [item.strip() for item in _RE_SENTENCE_SPLIT.split(cleaned) if item.strip()]
    if not sentences:
        return [cleaned[index:index + size].strip() for index in range(0, len(cleaned), size)]

    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(sentence) > size:
            if current:
                chunks.append(current)
                current = ""
            for index in range(0, len(sentence), size):
                part = sentence[index:index + size].strip()
                if part:
                    chunks.append(part)
            continue

        candidate = sentence if not current else f"{current} {sentence}"
        if len(candidate) <= size:
            current = candidate
        else:
            chunks.append(current)
            current = sentence

    if current:
        chunks.append(current)

    return chunks
