"""Document extraction helpers (EPUB/PDF)."""

import re
from typing import Optional

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
]

CHAPTER_PATTERNS = [
    r"^chapter\s+\d+",
    r"^chapter\s+one\b",
    r"^part\s+one\b",
    r"^1\s*$",
    r"^\d+\.\s+\w",
]


def is_front_matter(filename: str, title: str = "") -> bool:
    """Detect front/back matter sections by filename/title heuristics."""
    check = f"{filename} {title}".lower()
    for pattern in FRONT_MATTER_PATTERNS:
        if re.search(pattern, check, re.IGNORECASE):
            return True
    return False


def _extract_title(soup: object) -> str:
    for tag in ["h1", "h2", "title"]:
        heading = soup.find(tag)
        if heading:
            return heading.get_text(strip=True)
    return ""


def _word_count(text: str) -> int:
    cleaned = " ".join(text.split())
    return len(cleaned.split())


def _should_skip_initial_section(
    is_front: bool,
    word_count: int,
    found_chapter: bool,
    skip_count: int,
) -> bool:
    if found_chapter:
        return False
    return is_front or (word_count < 100 and skip_count < 5)


def _extract_pdf_text(reader: object, skip_pages: int) -> str:
    parts: list[str] = []
    for page in reader.pages[skip_pages:]:
        page_text = page.extract_text() or ""
        if page_text.strip():
            parts.append(page_text)

    text = "\n".join(parts).strip()
    if not text:
        text = "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    return text


def _find_content_start(lines: list[str]) -> int:
    for index, line in enumerate(lines[:100]):
        line_stripped = line.strip().lower()
        for pattern in CHAPTER_PATTERNS:
            if re.match(pattern, line_stripped):
                return index
    return 0


def extract_epub(path: str, config: TTSConfig) -> Optional[str]:
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
        skip_count = 0

        for filename, item in documents:
            soup = BeautifulSoup(item.get_content(), "html.parser")

            title = _extract_title(soup)

            is_front = is_front_matter(filename, title)

            text = soup.get_text(separator=" ")
            word_count = _word_count(text)

            if _should_skip_initial_section(is_front, word_count, found_chapter, skip_count):
                skip_count += 1
                if config.verbose:
                    print(f"  Skipping: {filename} ({word_count} words)")
                continue
            found_chapter = True

            for script in soup(["script", "style", "nav"]):
                script.decompose()

            text = " ".join(soup.get_text(separator=" ").split())
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


def extract_pdf(path: str, config: TTSConfig) -> Optional[str]:
    """Extract main text from PDF and trim likely preface/TOC lines."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(path)
        page_count = len(reader.pages)
        if page_count == 0:
            return None

        skip_pages = min(3, max(1, page_count // 10))
        text = _extract_pdf_text(reader, skip_pages)
        if not text:
            return None

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
