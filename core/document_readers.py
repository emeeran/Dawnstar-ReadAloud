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
    r"^\s*[\d]+\.\s+\w",
    r"^\s*i\.\s+\w",
]


def is_front_matter(filename: str, title: str = "") -> bool:
    """Detect front/back matter sections by filename/title heuristics."""
    check = f"{filename} {title}".lower()
    for pattern in FRONT_MATTER_PATTERNS:
        if re.search(pattern, check, re.IGNORECASE):
            return True
    return False


def _is_chapter_start(text: str) -> bool:
    """Check if text starts with a chapter-like heading."""
    lines = text.splitlines()
    # Check first few lines for a chapter heading
    for line in lines[:10]:
        line_stripped = line.strip().lower()
        if not line_stripped:
            continue
        for pattern in CHAPTER_PATTERNS:
            if re.match(pattern, line_stripped):
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


def _extract_pdf_text(reader: object, max_pages: int = 50) -> tuple[str, int]:
    """Extract text from PDF pages, looking for the first chapter."""
    parts: list[str] = []
    content_start_page = 0
    
    # Scan first few pages for chapter markers
    for i in range(min(len(reader.pages), max_pages)):
        page_text = reader.pages[i].extract_text() or ""
        if _is_chapter_start(page_text):
            content_start_page = i
            break
            
    # If no chapter marker found, default to skipping first few pages
    if content_start_page == 0 and len(reader.pages) > 5:
        content_start_page = min(3, len(reader.pages) // 10)

    for page in reader.pages[content_start_page:]:
        page_text = page.extract_text() or ""
        if page_text.strip():
            parts.append(page_text)

    return "\n".join(parts).strip(), content_start_page


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


def extract_pdf(path: str, config: TTSConfig) -> Optional[str]:
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
