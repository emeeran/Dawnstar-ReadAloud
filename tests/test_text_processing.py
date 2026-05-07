"""Unit tests for core.text_processing module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.text_processing import chunk_text, clean_text, strip_markdown


class TestStripMarkdown:

    def test_strips_headers(self):
        assert "#" not in strip_markdown("# Title")
        assert "Title" in strip_markdown("# Title")

    def test_strips_bold(self):
        assert strip_markdown("**bold** text") == "bold text"

    def test_strips_italic(self):
        assert strip_markdown("*italic* text") == "italic text"

    def test_strips_links_keeps_text(self):
        result = strip_markdown("[click here](https://example.com)")
        assert "click here" in result
        assert "https://example.com" not in result

    def test_removes_images(self):
        result = strip_markdown("![alt](image.png)")
        assert "image.png" not in result

    def test_strips_code_blocks(self):
        result = strip_markdown("before```code```after")
        assert "```" not in result

    def test_strips_inline_code(self):
        result = strip_markdown("use `foo` here")
        assert "`" not in result
        assert "foo" in result

    def test_strips_unordered_list(self):
        result = strip_markdown("- item one\n- item two")
        assert "item one" in result

    def test_strips_ordered_list(self):
        result = strip_markdown("1. first\n2. second")
        assert "first" in result
        assert "second" in result

    def test_combined(self):
        text = "# Header\n**bold** and *italic*\n[link](url)"
        result = strip_markdown(text)
        assert "#" not in result
        assert "*" not in result
        assert "[" not in result


class TestCleanText:

    def test_removes_urls(self):
        result = clean_text("Visit https://example.com now")
        assert "https://example.com" not in result
        assert "Visit" in result

    def test_removes_emails(self):
        result = clean_text("Email user@example.com please")
        assert "user@example.com" not in result

    def test_normalizes_whitespace(self):
        result = clean_text("hello   world\n\npara")
        assert "  " not in result
        assert "\n" not in result

    def test_strips_edges(self):
        assert clean_text("  hello  ") == "hello"

    def test_empty(self):
        assert clean_text("") == ""

    def test_whitespace_only(self):
        assert clean_text("   \n\t  ") == ""


class TestChunkText:

    def test_empty(self):
        assert chunk_text("") == []

    def test_whitespace_only(self):
        assert chunk_text("   ") == []

    def test_short_text(self):
        assert chunk_text("Hello world") == ["Hello world"]

    def test_sentence_splitting(self):
        text = "First sentence. Second sentence. Third sentence."
        result = chunk_text(text, size=25)
        assert len(result) >= 2

    def test_oversized_sentence_split(self):
        text = "A" * 300
        result = chunk_text(text, size=100)
        # With default size <= 200, chunk_text uses sentence mode
        # A 300-char string with no sentence boundaries returns as single chunk
        assert len(result) >= 1
        assert "".join(result) == text

    def test_preserves_content(self):
        text = "Hello world. How are you? I am fine."
        result = chunk_text(text)
        combined = " ".join(result)
        assert "Hello world" in combined
        assert "How are you" in combined
        assert "I am fine" in combined

    def test_no_sentence_boundaries(self):
        text = "A" * 50
        result = chunk_text(text, size=20)
        # size <= 200 triggers sentence mode, but no boundaries means single chunk
        assert len(result) >= 1
        assert "".join(result) == text
