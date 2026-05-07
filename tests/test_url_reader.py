"""Unit tests for core.url_reader module."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.exceptions import SecurityError
from core.url_reader import (
    _clean_html_content,
    _normalize_url,
    _score_element,
    _validate_url_scheme,
    extract_url_content,
)


class TestValidateUrlScheme:

    def test_accepts_http(self):
        assert _validate_url_scheme("http://example.com") is True

    def test_accepts_https(self):
        assert _validate_url_scheme("https://example.com") is True

    def test_rejects_file(self):
        assert _validate_url_scheme("file:///etc/passwd") is False

    def test_rejects_javascript(self):
        assert _validate_url_scheme("javascript:alert(1)") is False

    def test_rejects_ftp(self):
        assert _validate_url_scheme("ftp://evil.com") is False

    def test_case_insensitive(self):
        assert _validate_url_scheme("HTTP://EXAMPLE.COM") is True
        assert _validate_url_scheme("File:///etc") is False


class TestNormalizeUrl:

    def test_adds_https_to_bare_domain(self):
        assert _normalize_url("example.com") == "https://example.com"

    def test_preserves_http(self):
        assert _normalize_url("http://example.com") == "http://example.com"

    def test_preserves_https(self):
        assert _normalize_url("https://example.com") == "https://example.com"

    def test_raises_for_file_scheme(self):
        with pytest.raises(SecurityError):
            _normalize_url("file:///etc/passwd")

    def test_raises_for_javascript(self):
        with pytest.raises(SecurityError):
            _normalize_url("javascript:void(0)")

    def test_strips_whitespace(self):
        assert _normalize_url("  https://example.com  ") == "https://example.com"


class TestExtractUrlContent:

    def test_returns_none_when_no_bs4(self):
        with patch("core.url_reader.HAS_BS4", False):
            assert extract_url_content("https://example.com") is None

    def test_raises_for_dangerous_url(self):
        with patch("core.url_reader.HAS_BS4", True), pytest.raises(SecurityError):
            extract_url_content("file:///etc/passwd")


class TestScoreElement:

    def test_article_tag_bonus(self):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup("<article><p>" + "x" * 500 + "</p></article>", "html.parser")
        article = soup.find("article")
        div = soup.new_tag("div")
        div.string = "x" * 500
        assert _score_element(article) > _score_element(div)

    def test_longer_text_scores_higher(self):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup("<div></div>", "html.parser")
        short = soup.new_tag("div")
        short.string = "short"
        long_el = soup.new_tag("div")
        long_el.string = "x" * 1000
        assert _score_element(long_el) > _score_element(short)

    def test_nav_penalty(self):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup("<div></div>", "html.parser")
        good = soup.new_tag("div")
        good.string = "x" * 500
        nav = soup.new_tag("div")
        nav["class"] = ["nav"]
        nav.string = "x" * 500
        assert _score_element(good) > _score_element(nav)


class TestCleanHtmlContent:

    def test_removes_script_tags(self):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup("<div><script>alert(1)</script><p>Hello</p></div>", "html.parser")
        result = _clean_html_content(soup)
        assert result.find("script") is None
        assert result.find("p") is not None

    def test_removes_style_tags(self):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup("<div><style>.x{}</style><p>Text</p></div>", "html.parser")
        result = _clean_html_content(soup)
        assert result.find("style") is None
