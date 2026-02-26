"""Web article extraction utilities."""

import re
import urllib.request
from typing import Optional

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

# Elements to skip (navigation, ads, sidebars, etc.)
SKIP_TAGS = {
    'nav', 'header', 'footer', 'aside', 'script', 'style',
    'form', 'iframe', 'noscript', 'svg', 'button', 'input',
    'select', 'textarea', 'menu', 'menuitem'
}

# Class/ID patterns that indicate non-content areas
SKIP_PATTERNS = [
    r'nav', r'menu', r'sidebar', r'footer', r'header',
    r'comment', r'share', r'social', r'related', r'recommend',
    r'advertisement', r'ad-', r'ads-', r'promo', r'sponsor',
    r'breadcrumb', r'pagination', r'author-info', r'tag[s]?$',
    r'newsletter', r'subscribe', r'popup', r'modal', r'overlay',
    r'cookie', r'gdpr', r'privacy', r'login', r'signup',
    r'search', r'filter', r'sort', r'widget'
]

# Patterns that indicate main content
CONTENT_PATTERNS = [
    r'article', r'content', r'post', r'entry', r'story',
    r'body', r'main', r'text', r'blog', r'news'
]


def _clean_text(text: str) -> str:
    """Clean and normalize text."""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    # Remove common junk
    text = re.sub(r'Subscribe\s*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Newsletter\s*$', '', text, flags=re.IGNORECASE)
    return text.strip()


def _score_element(elem) -> int:
    """Score an element's likelihood of being main content."""
    if elem is None or elem.name is None:
        return 0

    score = 0

    # Check tag name
    if elem.name in ['article', 'main']:
        score += 50
    elif elem.name == 'div':
        score += 10

    # Check class/id for content hints
    classes = ' '.join(elem.get('class', []) or [])
    elem_id = elem.get('id', '') or ''
    combined = f"{classes} {elem_id}".lower()

    for pattern in CONTENT_PATTERNS:
        if re.search(pattern, combined, re.IGNORECASE):
            score += 30

    # Score by text length (more text = more likely main content)
    try:
        text_len = len(elem.get_text(strip=True))
        score += min(text_len / 50, 100)  # Cap at 100
    except:
        pass

    # Penalize for too many links (nav areas have lots of links)
    try:
        links = elem.find_all('a')
        text = elem.get_text(strip=True)
        if text:
            link_density = len(links) / (len(text.split()) + 1)
            if link_density > 0.3:
                score -= 30
    except:
        pass

    # Bonus for paragraph tags (article content has <p>)
    try:
        paragraphs = elem.find_all('p')
        score += len(paragraphs) * 5
    except:
        pass

    return score


def extract_url_content(url: str, timeout: int = 20) -> Optional[str]:
    """Fetch URL and extract main article content."""
    if not HAS_BS4:
        return None

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; TTS-Reader/1.0)'}
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            html = response.read().decode('utf-8', errors='ignore')
    except Exception:
        return None

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
                is_toc = "table of contents" in text_preview or "contents" == text_preview
                
                for pattern in SKIP_PATTERNS:
                    # Don't decompose if it's a main-looking ID/class
                    if any(p in combined for p in ['main', 'article', 'body-content']):
                        continue

                    if re.search(pattern, combined, re.IGNORECASE) or is_toc:
                        elem.decompose()
                        break
            except:
                continue

    # Try to find main content area
    candidates = []

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
        except:
            continue

    if not candidates:
        main = soup.find('body')
    else:
        main = max(candidates, key=_score_element, default=soup.find('body'))

    if not main:
        return None

    # Extract text from paragraphs and headings
    parts = []
    for elem in main.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li']):
        try:
            text = _clean_text(elem.get_text())
            if len(text) > 20:
                parts.append(text)
        except:
            continue

    return ' '.join(parts) if parts else None
