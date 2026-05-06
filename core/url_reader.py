"""Web article extraction utilities.

This module provides safe URL fetching and article content extraction
with protection against malicious URLs and HTML parsing attacks.
"""

import json
import re
import urllib.request
from urllib.error import URLError

try:
    from bs4 import BeautifulSoup, Tag
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

from .config import TTSConfig
from .exceptions import SecurityError
from .logger import Logger

# Allowed URL schemes - only HTTP/HTTPS permitted for security
ALLOWED_SCHEMES = ('http://', 'https://')

# Size limits
_MAX_URL_SIZE = 10 * 1024 * 1024  # 10 MB
_HTML_CONTENT_SIZE_LIMIT = 100 * 1024  # 100 KB (fixed from incorrect 100*100)

# Content thresholds (configurable via constants)
_MIN_CONTENT_LENGTH = 400  # Minimum text length to consider as main content
_MIN_TEXT_LENGTH = 20  # Minimum text length to include a paragraph

# HTML tags to remove completely
SKIP_TAGS = ['script', 'style', 'noscript', 'iframe', 'svg', 'canvas', 'object', 'embed', 'form']

# Classes/IDs that indicate MAIN content (never remove these)
_MAIN_CONTENT_MARKERS = [
    'post-content', 'entry-content', 'main-content',
    'article-content', 'article-body', 'story-body',
    'post-body', 'entry-body', 'content-body',
    'page-content', 'blog-content', 'news-content',
    'article__body', 'story-content',
]

# Patterns for identifying non-content elements to remove
_COMPILED_SKIP_PATTERNS = [
    re.compile(r'(?:comment|feedback|footer|menu|nav|sidebar)\b', re.IGNORECASE),
    re.compile(r'\barticle\b.*?[\s]*tags?\]', re.IGNORECASE),
    re.compile(r'\bread-next\b.*?\s*<\d.*', re.IGNORECASE),
    re.compile(r'\bread-more\b.*?\s*<\d.*', re.IGNORECASE),
    re.compile(r'\breply\b.*?\s*<\d.*', re.IGNORECASE),
    re.compile(r'\bcomment-form\b.*?\s*<\d.*', re.IGNORECASE),
    re.compile(r'\bcomment(s?-form)?\b', re.IGNORECASE),
    re.compile(r'\bpublished\b.*?\s*<\d.*', re.IGNORECASE),
    re.compile(r'\bcopyright\b.*?\s*<\d.*', re.IGNORECASE),
    re.compile(r'\bsocial\s*hare|share|repost|newsletter|promo|signup|sponsored|testimonial\b', re.IGNORECASE),
]

# HTTP headers for requests
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; TTS-Reader/1.0)",
    "Accept": "text/html,application/xhtml+xml",
}

def _validate_url_scheme(url: str) -> bool:
    """Validate that URL uses an allowed scheme (HTTP/HTTPS only).

    Args:
        url: URL to validate.

    Returns:
        True if scheme is allowed, False otherwise.
    """
    url_lower = url.lower().strip()
    return any(url_lower.startswith(scheme) for scheme in ALLOWED_SCHEMES)


def _normalize_url(url: str) -> str:
    """Normalize URL by adding HTTPS scheme if missing.

    Args:
        url: URL to normalize.

    Returns:
        Normalized URL with https:// prefix if no scheme present.

    Raises:
        SecurityError: If URL has invalid/dangerous scheme.
    """
    url = url.strip()

    # Check for dangerous schemes first
    if ':' in url.split('/')[0]:  # Has a scheme
        if not _validate_url_scheme(url):
            raise SecurityError(
                f"Invalid URL scheme - only HTTP/HTTPS allowed. "
                f"Blocked: {url[:50]}..."
            )
        return url

    # No scheme - add HTTPS
    return 'https://' + url


def _fetch_url_html(url: str, timeout: int, config: TTSConfig) -> str | None:
    """Fetch HTML content from URL with validation.

    Args:
        url: URL to fetch.
        timeout: Request timeout in seconds.
        config: TTS configuration for logging.

    Returns:
        HTML content as string, or None if fetch failed.
    """
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        req.add_header("Accept", "text/html")

        with urllib.request.urlopen(req, timeout=timeout) as response:
            # Check content-length if available
            content_length = response.headers.get('Content-Length')
            if content_length and int(content_length) > _MAX_URL_SIZE:
                Logger.log(f"Content too large ({content_length} bytes)", config)
                return None

            html = response.read(_MAX_URL_SIZE).decode('utf-8', errors='ignore')
            return html

    except (URLError, urllib.error.URLError) as e:
        Logger.log(f"URL fetch error: {e}", config)
        return None
    except (OSError, ValueError) as e:
        Logger.log(f"URL connection error: {e}", config)
        return None


def _should_remove_element(elem) -> bool:
    """Check if element should be removed based on content patterns.

    Args:
        elem: BeautifulSoup element to check.

    Returns:
        True if element should be removed, False otherwise.
    """
    try:
        classes = ' '.join(elem.get('class', []) or [])
        elem_id = elem.get('id', '') or ''
        text_preview = elem.get_text(strip=True)[:50].lower()
        combined = f"{classes} {elem_id}".lower()

        # Never remove main content markers (post-content, entry-content, etc.)
        for marker in _MAIN_CONTENT_MARKERS:
            if marker in combined:
                return False

        # Never remove semantic content elements
        if any(p in combined for p in ['main', 'article', 'body-content', 'content']):
            return False

        # Never remove role="main" or role="article"
        role = elem.get('role', '') or ''
        if role in ('main', 'article', 'contentinfo'):
            return False

        # Check against skip patterns
        for pattern in _COMPILED_SKIP_PATTERNS:
            if pattern.search(combined):
                return True

        # Skip "Table of Contents" blocks
        if "table of contents" in text_preview or text_preview == "contents":
            return True

    except (AttributeError, RuntimeError):
        pass

    return False


def _clean_html_content(soup: BeautifulSoup) -> BeautifulSoup:
    """Remove unwanted elements from HTML.

    Args:
        soup: BeautifulSoup object to clean.

    Returns:
        Cleaned BeautifulSoup object.
    """
    # Remove script, style, and other non-content tags
    for tag in SKIP_TAGS:
        for elem in soup.find_all(tag):
            elem.decompose()

    # Remove elements matching skip patterns
    for tag in ['div', 'section', 'nav', 'header', 'footer', 'aside', 'ul', 'ol']:
        for elem in soup.find_all(tag):
            if _should_remove_element(elem):
                elem.decompose()

    return soup


def _find_main_content(soup: BeautifulSoup) -> Tag | None:
    """Find the main content area of the page.

    Args:
        soup: BeautifulSoup object.

    Returns:
        Main content element, or body if not found.
    """
    candidates: list[Tag] = []

    # Look for semantic content containers (ordered by specificity)
    selectors = [
        # Semantic HTML5
        'article', 'main', '[role="main"]',
        # Wikipedia
        '#mw-content-text',
        # WordPress / Ghost / common CMS
        '.post-content', '.article-content', '.entry-content',
        '.post-body', '.article-body', '.story-body',
        # Generic content containers
        '.content', '#content', '#main',
        # News sites
        '.story-content', '.news-content',
        # Medium / Substack
        'section > div > article',
    ]

    for selector in selectors:
        candidates.extend(soup.select(selector))

    # Score all divs/sections as potential content
    for elem in soup.find_all(['div', 'section']):
        try:
            classes = ' '.join(elem.get('class', []) or [])
            elem_id = elem.get('id', '') or ''
            combined = f"{classes} {elem_id}".lower()

            # Skip known non-content elements
            if any(m in combined for m in ['sidebar', 'widget', 'promo', 'ad-', 'advert']):
                continue

            text_len = len(elem.get_text(strip=True))
            if text_len > _MIN_CONTENT_LENGTH:
                candidates.append(elem)
        except (AttributeError, TypeError):
            continue

    if not candidates:
        return soup.find('body')

    return max(candidates, key=_score_element, default=soup.find('body'))


def _clean_text(text: str) -> str:
    """Clean extracted text by normalizing whitespace.

    Args:
        text: Raw text from HTML element.

    Returns:
        Cleaned text with normalized whitespace.
    """
    return ' '.join(text.split())


def _extract_text_from_element(elem: Tag) -> str | None:
    """Extract clean text from content element.

    Extracts text from paragraphs, headings, and list items while
    skipping very short fragments (likely labels, captions, etc.).

    Args:
        elem: BeautifulSoup element to extract text from.

    Returns:
        Extracted text, or None if no text found.
    """
    parts: list[str] = []

    # Capture headings, paragraphs, list items, and blockquotes
    for child in elem.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li', 'blockquote']):
        try:
            text = _clean_text(child.get_text())
            # Headings can be shorter than _MIN_TEXT_LENGTH
            is_heading = child.name in ('h1', 'h2', 'h3', 'h4')
            if len(text) > _MIN_TEXT_LENGTH or (is_heading and len(text) > 5):
                parts.append(text)
        except (AttributeError, TypeError):
            continue

    # Fallback: if no structured elements found, get all text
    if not parts:
        full_text = _clean_text(elem.get_text())
        if len(full_text) > _MIN_CONTENT_LENGTH:
            return full_text

    return ' '.join(parts) if parts else None


def _score_element(elem: Tag) -> float:
    """Score an element based on likelihood of being main content.

    Args:
        elem: BeautifulSoup element to score.

    Returns:
        Score (higher = more likely to be main content).
    """
    text = elem.get_text(strip=True)
    score = float(len(text))

    # Bonus for semantic content tags
    if elem.name in ('article', 'main'):
        score *= 2

    # Bonus for main content markers in class/id
    classes = ' '.join(elem.get('class', []) or []).lower()
    elem_id = (elem.get('id', '') or '').lower()
    combined = f"{classes} {elem_id}"

    for marker in _MAIN_CONTENT_MARKERS:
        if marker in combined:
            score *= 2
            break

    # Bonus for containing paragraph tags (articles have many <p>)
    p_count = len(elem.find_all('p'))
    if p_count > 3:
        score *= 1.5

    # Penalty for navigation-like elements
    if any(x in classes for x in ['nav', 'menu', 'sidebar', 'widget', 'promo', 'ad-']):
        score /= 2

    return score


def _extract_json_ld_article(soup: BeautifulSoup) -> str | None:
    """Extract article text from JSON-LD structured data.

    Many news sites embed article content in JSON-LD schema.org markup.
    This provides a fallback when the main content isn't in static HTML.

    Args:
        soup: BeautifulSoup object.

    Returns:
        Article text from JSON-LD, or None if not found.
    """
    import html

    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string)
            # Handle NewsArticle schema
            if isinstance(data, dict):
                if data.get('@type') in ('NewsArticle', 'Article'):
                    parts = []
                    if data.get('headline'):
                        parts.append(data['headline'])
                    if data.get('description'):
                        parts.append(data['description'])
                    if data.get('articleBody'):
                        parts.append(data['articleBody'])
                    if parts:
                        text = ' '.join(parts)
                        # Unescape HTML entities and strip remaining HTML tags
                        text = html.unescape(text)
                        text = re.sub(r'<[^>]+>', '', text)  # Remove any HTML tags
                        return text
                # Handle nested @graph
                if '@graph' in data:
                    for item in data['@graph']:
                        if isinstance(item, dict) and item.get('@type') in ('NewsArticle', 'Article'):
                            parts = []
                            if item.get('headline'):
                                parts.append(item['headline'])
                            if item.get('description'):
                                parts.append(item['description'])
                            if item.get('articleBody'):
                                parts.append(item['articleBody'])
                            if parts:
                                text = ' '.join(parts)
                                text = html.unescape(text)
                                text = re.sub(r'<[^>]+>', '', text)
                                return text
        except (json.JSONDecodeError, TypeError, AttributeError):
            continue
    return None


def extract_url_content(url: str, timeout: int = 20, config: TTSConfig | None = None) -> str | None:
    """Fetch URL and extract main article content.

    This function safely fetches web content by:
    1. Validating URL scheme (only HTTP/HTTPS allowed)
    2. Limiting response size to prevent DoS
    3. Removing ads, navigation, and boilerplate
    4. Extracting main article text using heuristics

    Args:
        url: URL to fetch content from.
        timeout: Request timeout in seconds (default: 20).
        config: TTS configuration for verbose logging.

    Returns:
        Extracted article text, or None if extraction failed.

    Raises:
        SecurityError: If URL has invalid/dangerous scheme.
    """
    if not HAS_BS4:
        return None

    # Create a minimal config if none provided
    if config is None:
        config = TTSConfig()

    # SECURITY: Validate and normalize URL scheme
    try:
        url = _normalize_url(url)
    except SecurityError:
        Logger.log(f"Blocked URL with invalid scheme: {url[:50]}", config)
        raise

    # Fetch HTML content
    html = _fetch_url_html(url, timeout, config)
    if not html:
        return None

    # Parse HTML
    soup = BeautifulSoup(html, 'html.parser')

    # Try JSON-LD structured data first (for dynamically loaded content)
    json_ld_text = _extract_json_ld_article(soup)
    if json_ld_text and len(json_ld_text) > _MIN_CONTENT_LENGTH:
        Logger.log(f"Extracted from JSON-LD: {len(json_ld_text)} chars", config)
        return json_ld_text

    # Clean HTML (remove ads, nav, etc.)
    soup = _clean_html_content(soup)

    # Find main content area
    main = _find_main_content(soup)
    if not main:
        return None

    # Extract text from content
    return _extract_text_from_element(main)
