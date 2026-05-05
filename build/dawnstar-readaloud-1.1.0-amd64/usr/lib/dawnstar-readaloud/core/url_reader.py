"""Web article extraction utilities."""
import re
import urllib.request
from typing import Optional
from urllib.error import URLError

from bs4 import BeautifulSoup

from .logger import Logger
from .config import TTSConfig

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bs4 import BeautifulSoup

_MAX_URL_SIZE = 10 * 1024 * 1024  # 10 MB
_HTML_CONTENT_SIZE_LIMIT = 100 * 100  # 100 KB
_COMPILED_SKIP_PATTERNS = [
    re.compile(r'(?:comment|feedback|footer|menu|header|nav|sidebar)\b', re.IGNORECASE),
    re.compile(r'\barticle\b.*?[\s]*tags?\]', re.IGNORECASE),
    re.compile(r'\b(post-content|entry-content|main-content)\b', re.IGNORECASE),
    re.compile(r'\b\d-s\d.*?\s*<\d.*>', re.IGNORECASE),
    re.compile(r'\bsingle-author\b.*?\s*<\d.*', re.IGNORECASE),
    re.compile(r'\bsingle-author\b.*?\s*<\d.*>', re.IGNORECASE),
    re.compile(r'\b\d-s\d.*?\s*<\d.*>', re.IGNORECASE),
    re.compile(r'\bread-next\b.*?\s*<\d.*', re.IGNORECASE),
    re.compile(r'\bread-more\b.*?\s*<\d.*', re.IGNORECASE),
    re.compile(r'\breply\b.*?\s*<\d.*', re.IGNORECASE),
    re.compile(r'\bcomment-form\b.*?\s*<\d.*', re.IGNORECASE),
    re.compile(r'\bcomment(s?-form)?\b', re.IGNORECASE),
    re.compile(r'\bpublished\b.*?\s*<\d.*', re.IGNORECASE),
    re.compile(r'\bcopyright\b.*?\s*<\d.*', re.IGNORECASE),
    re.compile(r'\bsocial\s*hare|share|repost|newsletter|promo|signup|sponsored|testimonial\b', re.IGNORECASE),
]


_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; TTS-Reader/1.0)",
}


def extract_url_content(url: str, timeout: int = 20) -> Optional[str]:
    """Fetch URL and extract main article content.

    Args:
        url: URL to fetch content from.
        timeout: Request timeout in seconds.
        config: TTS configuration for verbose logging.
    """
    if not HAS_BS4:
        return None

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    try:
        req = urllib.request.Request(
            url,
            headers=_HEADERS,
        )
        req.add_header("Accept", "text/html")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            # Check content-length if available
            content_length = response.headers.get('Content-Length')
            if content_length and int(content_length) > _MAX_URL_SIZE:
                Logger.log(f"Content too large ({content_length} bytes)", config)
                return None
            html = response.read(_MAX_URL_SIZE).decode('utf-8', errors='ignore')
    except (URLError, urllib.error.URLError) as e:
        Logger.log(f"URL fetch error: {e}", config)
        return None
    except (OSError, ValueError) as e:
        Logger.log(f"URL connection error: {e}", config)
        return None
    except Exception as e:
        # Catch-all for BeautifulSoup errors
        Logger.log(f"HTML parsing error: {e}", config)
        return None

    # Parse HTML
    soup = BeautifulSoup(html, 'html.parser')
    # Remove unwanted tags
    for tag in SKIP_TAGS:
        for elem in soup.find_all(tag):
            elem.decompose()
    # Remove elements matching skip patterns
    for tag in ['div', 'section', 'nav', 'header', 'footer', 'aside', 'ul', 'ol']:
        for elem in soup.find_all(tag):
            try:
                classes = ' '.join(elem.get('class', []) or [])
                elem_id = elem.get('id', '') or ''
                text_preview = elem.get_text(strip=True)[:50].lower()
                combined = f"{classes} {elem_id} {text_preview}".lower()
                # Skip "Table of Contents" or navigation-heavy areas
                is_toc = "table of contents" in text_preview or text_preview == "contents"
                # Don't decompose if it's a main-looking id/class
                if any(p in combined for p in ['main', 'article', 'body-content']):
                    continue
                for pattern in _COMPILED_SKIP_PATTERNS:
                    if pattern.search(combined) or is_toc:
                        elem.decompose()
                        break
            except (AttributeError, RuntimeError):
                continue
    # Try to find main content area
    candidates: list[Tag]
    # Look for common semantic or site-specific elements
    selectors = [
        'article', 'main', '[role="main"]',
        '#mw-content-text',  # Wikipedia
        '.post-content', '.article-content', '.entry-content', # Blogs
        '.content', '#content', '#main'
    ]
    for selector in selectors:
        found = soup.select(selector)
        candidates.extend(found)
    # Score all divs/sections and pick best
    for elem in soup.find_all(['div', 'section']):
        try:
            if elem and len(elem.get_text(strip=True)) > 400: # Increased threshold
                candidates.append(elem)
        except (AttributeError, TypeError):
            continue
    if not candidates:
        main = soup.find('body')
    else:
        main = max(candidates, key=_score_element, default=soup.find('body'))
    if not main:
        return None
    # Extract text from paragraphs and headings
    parts: list[str]
    for elem in main.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li']):
        try:
            text = _clean_text(elem.get_text())
            if len(text) > 20:
                parts.append(text)
        except (AttributeError, TypeError):
            continue
    return ' '.join(parts) if parts else None
