"""Document extraction helpers (EPUB/PDF)."""

import re

from .config import TTSConfig
from .logger import Logger

__all__ = [
    "FRONT_MATTER_PATTERNS",
    "is_front_matter",
    "extract_epub",
    "extract_pdf",
]

FRONT_MATTER_PATTERNS = [
    r"(?:^|[/\s])toc(?:[/\s\.]|$)",
    r"table\s+of\s+contents?",
    r"\bpreface\b",
    r"\bforeword\b",
    r"\bprologue\b",
    r"\bcopyright\b",
    r"\bdedication\b",
    r"about\s+the\s+author",
    r"about\s+the\s+publisher",
    r"\backnowledge?ments?\b",
    r"\bcredits\b",
    r"\bcover(?:\s+page)?\b",
    r"\btitle\s+page\b",
    r"\bepigraph\b",
    r"\bfrontispiece\b",
    r"series\s+page",
    r"also\s+by\s+\w",
    r"praise\s+for",
    r"advanced\s+praise",
    r"\bendorsements?\b",
    r"\bappendix\b",
    r"\bbibliography\b",
    r"\bindex\b",
    r"\bglossary\b",
    r"\breferences?\b",
    r"\bmap\b",
    r"author'?s\s+note",
    r"title\s+page",
    r"half\s+title",
]

CHAPTER_PATTERNS = [
    r"^\s*chapter\s+(?:one|[\d\w]+)\b",
    r"^\s*part\s+(?:one|[\d\w]+)\b",
    r"^\s*introduction\b",
    r"^\s*book\s+(?:one|[\d\w]+)\b",
]

# Stricter pattern for numbered chapters - requires substantial text, no trailing dots
NUMBERED_CHAPTER_PATTERN = re.compile(r"^\s*[\d]+\.\s+[A-Z][^.]{20,}$")
# Pattern to detect TOC-style trailing dots
_TOC_DOTS_PATTERN = re.compile(r"\.\s+\.\s+\.")

# Pre-compiled patterns for performance
_COMPILED_FRONT_MATTER = [re.compile(p, re.IGNORECASE) for p in FRONT_MATTER_PATTERNS]
_COMPILED_CHAPTER = [re.compile(p) for p in CHAPTER_PATTERNS]


def is_front_matter(filename: str, title: str = "") -> bool:
    """Detect front/back matter sections by filename/title heuristics."""
    check = f"{filename} {title}".lower()
    return any(pattern.search(check) for pattern in _COMPILED_FRONT_MATTER)


def _is_chapter_start(text: str) -> bool:
    """Check if text starts with a chapter-like heading."""
    return _find_chapter_line(text.splitlines()) >= 0


def _find_chapter_line(lines: list[str], max_lines: int = 20) -> int:
    """Find the first line that matches a chapter heading pattern.

    Args:
        lines: Lines of text to search.
        max_lines: Maximum number of lines to check (reduced to avoid false positives).

    Returns:
        Index of the first chapter-heading line, or -1 if not found.
    """
    for index, line in enumerate(lines[:max_lines]):
        stripped = line.strip()
        if not stripped:
            continue

        # Skip TOC-style lines
        if _TOC_DOTS_PATTERN.search(stripped):
            continue

        # Check for explicit "CHAPTER X" format (case insensitive)
        if re.match(r'^CHAPTER\s+[\d\w]+', stripped, re.IGNORECASE):
            return index

        # Check for numbered chapter "1. Title" format
        if NUMBERED_CHAPTER_PATTERN.match(stripped):
            return index

        # Check for "Introduction" as standalone heading
        if re.match(r'^introduction\s*$', stripped.lower()):
            return index

    return -1


def _extract_title(soup: object) -> str:
    for tag in ["h1", "h2", "title"]:
        heading = soup.find(tag)
        if heading:
            return heading.get_text(strip=True)
    return ""


def _word_count(text: str) -> int:
    return len(text.split())


def _should_skip_initial_section(
    is_front: bool,
    word_count: int,
    found_chapter: bool,
    text_preview: str,
) -> bool:
    if found_chapter:
        return False

    # If it's explicitly front matter, skip it
    if is_front:
        return True

    # Check if this section starts with a chapter heading
    if _is_chapter_start(text_preview):
        return False

    # Skip small sections that aren't chapters
    return word_count < 250


def _has_toc_dotted_lines(page_text: str) -> bool:
    """Detect if page has table of contents style dotted lines.

    TOC pages have patterns like:
    - "Chapter 1 ......... 10" (continuous dots)
    - "Chapter 1 . . . . . . . . . . . . . 10" (spaced dots)
    """
    # Pattern 1: Continuous dots (5+)
    continuous_dots = re.compile(r"\.{5,}")
    # Pattern 2: Spaced dots (at least 6 dots with spaces between)
    spaced_dots = re.compile(r"(?:\.\s*){6,}")

    continuous_matches = continuous_dots.findall(page_text)
    spaced_matches = spaced_dots.findall(page_text)

    return len(continuous_matches) >= 2 or len(spaced_matches) >= 2


def _extract_pdf_text(reader: object, max_pages: int = 50) -> tuple[str, int]:
    """Extract text from PDF pages, looking for the first chapter.

    Skips TOC, preface, and other front matter to start from Chapter 1.
    """
    parts: list[str] = []
    content_start_page = 0
    found_chapter = False

    # First pass: find the first real chapter (skip TOC, preface, etc.)
    for i in range(min(len(reader.pages), max_pages)):
        page_text = reader.pages[i].extract_text() or ""

        # Skip pages with TOC-style dotted lines
        if _has_toc_dotted_lines(page_text):
            content_start_page = i + 1
            continue

        # Skip pages with very little text (title/copyright pages)
        word_count = len(page_text.split())
        if word_count < 150:
            content_start_page = i + 1
            continue

        # Look for explicit chapter markers
        if _is_chapter_start(page_text):
            content_start_page = i
            found_chapter = True
            break

        # If we find substantial content without chapter marker,
        # check if it looks like preface/intro vs actual chapter
        if word_count >= 500:
            # Check for preface indicators in first 500 chars
            preview = page_text[:500].lower()
            if any(indicator in preview for indicator in [
                'preface', 'acknowled', 'foreword', 'introduction to this book',
                'how to read', 'who should read', 'conventions used'
            ]):
                content_start_page = i + 1
                continue

            # Found substantial non-chapter content, keep looking
            if not found_chapter:
                content_start_page = i + 1

    # If no chapter found, default to skipping first 10% or 5 pages
    if not found_chapter and len(reader.pages) > 5:
        content_start_page = max(content_start_page, min(5, len(reader.pages) // 10))

    for page in reader.pages[content_start_page:]:
        page_text = page.extract_text() or ""
        if page_text.strip():
            parts.append(page_text)

    return "\n".join(parts).strip(), content_start_page


def _find_content_start(lines: list[str]) -> int:
    """Find the first line that looks like chapter content."""
    result = _find_chapter_line(lines, max_lines=100)
    return result if result >= 0 else 0


def extract_epub(path: str, config: TTSConfig) -> str | None:
    """Extract main text from EPUB, skipping likely front matter."""
    try:
        import ebooklib
        from bs4 import BeautifulSoup
        from ebooklib import epub

        book = epub.read_epub(path)
        documents = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                filename = item.get_name() or item.get_id() or ""
                documents.append((filename, item))

        main_content: list[str] = []
        found_chapter = False

        for filename, item in documents:
            soup = BeautifulSoup(item.get_content(), "html.parser")

            # Clean soup before word count
            for script in soup(["script", "style", "nav"]):
                script.decompose()

            title = _extract_title(soup)
            is_front = is_front_matter(filename, title)

            text = " ".join(soup.get_text(separator=" ").split())
            word_count = _word_count(text)

            if _should_skip_initial_section(is_front, word_count, found_chapter, text[:500]):
                if config.verbose:
                    print(f"  Skipping: {filename} ({word_count} words)")
                continue

            found_chapter = True
            if text.strip() and word_count >= 20:
                main_content.append(text.strip())

        return " ".join(main_content)

    except ImportError:
        Logger.log("ebooklib or beautifulsoup4 required for EPUB support", config)
        print("Install with: pip install ebooklib beautifulsoup4")
        return None
    except (OSError, ValueError, KeyError, AttributeError) as error:
        Logger.log(f"EPUB read error: {error}", config)
        return None


def extract_pdf(path: str, config: TTSConfig) -> str | None:
    """Extract main text from PDF and trim likely preface/TOC lines."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(path)
        page_count = len(reader.pages)
        if page_count == 0:
            return None

        text, start_page = _extract_pdf_text(reader)
        if not text:
            return None

        if config.verbose:
            print(f"  Starting PDF content from page {start_page + 1}")

        lines = text.split("\n")
        content_start = _find_content_start(lines)

        if content_start > 0:
            text = "\n".join(lines[content_start:])

        return text

    except ImportError:
        Logger.log("pypdf required for PDF support", config)
        print("Install with: pip install pypdf")
        return None
    except (OSError, ValueError) as error:
        Logger.log(f"PDF read error: {error}", config)
        return None
