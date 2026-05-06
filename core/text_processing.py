"""Text cleaning and chunking helpers."""

import re

from .constants import CHUNK_SIZE

__all__ = ["clean_text", "chunk_text"]

_RE_URL = re.compile(r"http[s]?://\S+")
_RE_EMAIL = re.compile(r"\S+@\S+")
_RE_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
# Match newlines and multiple spaces
_RE_WHITESPACE = re.compile(r"\s+")

# Markdown stripping patterns
_RE_MD_HEADER = re.compile(r"^#+\s+", re.MULTILINE)
_RE_MD_BOLD_ITALIC = re.compile(r"[*_]{1,3}")
_RE_MD_LINK = re.compile(r"\[([^\]]+)\]\([^\)]*\)")
_RE_MD_IMAGE = re.compile(r"!\[[^\]]*\]\([^\)]*\)")
_RE_MD_CODE_BLOCK = re.compile(r"```[\s\S]*?```")
_RE_MD_INLINE_CODE = re.compile(r"`([^`]+)`")
_RE_MD_LIST_MARKER = re.compile(r"^\s*[-*+]\s+", re.MULTILINE)
_RE_MD_NUM_LIST_MARKER = re.compile(r"^\s*\d+\.\s+", re.MULTILINE)


def strip_markdown(text: str) -> str:
    """Remove common Markdown symbols while preserving readable text content.

    Converts Markdown to spoken-friendly format:
    - Headers: Add pause indicator (preserved as natural break)
    - Bold/italic: Remove markers, keep text
    - Links: Keep link text, remove URL
    - Lists: Remove bullets, keep items
    - Code: Remove backticks, keep code text
    """
    # Convert headers to plain text with spacing (preserves structure for pauses)
    text = _RE_MD_HEADER.sub(lambda m: "\n" + " ".join(m.group(0).lstrip("# ").split()) + "\n", text)

    # Remove image markup entirely (not useful for TTS)
    text = _RE_MD_IMAGE.sub("", text)

    # Convert links to just the link text
    text = _RE_MD_LINK.sub(r"\1", text)

    # Remove code blocks but preserve content
    text = _RE_MD_CODE_BLOCK.sub(
        lambda m: m.group(0).removeprefix("```").removesuffix("```").strip() + "\n", text
    )

    # Remove inline code backticks
    text = _RE_MD_INLINE_CODE.sub(r"\1", text)

    # Remove bold/italic markers
    text = _RE_MD_BOLD_ITALIC.sub("", text)

    # Remove list markers
    text = _RE_MD_LIST_MARKER.sub("", text)
    text = _RE_MD_NUM_LIST_MARKER.sub("", text)

    return text


def clean_text(text: str) -> str:
    """Remove Markdown symbols, URLs/emails, and normalize whitespace.

    Normalizes whitespace for smooth TTS:
    - Collapses multiple spaces/tabs to single space
    - Converts newlines to space (fixes PDF line breaks and markdown)
    """
    # Strip Markdown symbols FIRST (to handle links [text](url) properly)
    text = strip_markdown(text)

    # Then strip "naked" URLs and Emails
    text = _RE_URL.sub("", text)
    text = _RE_EMAIL.sub("", text)

    # Collapse all whitespace (newlines, tabs, multiple spaces) to single space
    text = _RE_WHITESPACE.sub(" ", text)

    return text.strip()


def chunk_text(text: str, size: int = CHUNK_SIZE) -> list[str]:
    """Split text into chunks, prioritizing single sentences for better highlighting."""
    cleaned = text.strip()
    if not cleaned:
        return []

    # If size is small (e.g., 1-200), we treat it as "sentence mode"
    sentences = [item.strip() for item in _RE_SENTENCE_SPLIT.split(cleaned) if item.strip()]
    if not sentences:
        return [cleaned[index:index + size].strip() for index in range(0, len(cleaned), size)]

    if size <= 200:
        # Sentence-by-sentence mode
        return sentences

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
