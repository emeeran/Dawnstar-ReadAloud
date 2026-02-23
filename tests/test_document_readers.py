"""Unit tests for core.document_readers helpers."""

from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.document_readers import (
    _find_content_start,
    _should_skip_initial_section,
    is_front_matter,
)


def test_is_front_matter_detects_toc_filename() -> None:
    """Front matter detector should identify TOC-like filenames."""
    assert is_front_matter("toc.xhtml") is True


def test_is_front_matter_detects_title_pattern() -> None:
    """Front matter detector should identify front-matter section titles."""
    assert is_front_matter("chapter1.xhtml", "Preface") is True


def test_should_skip_initial_section_for_short_initial_chunk() -> None:
    """Initial short chunks should be skipped before first chapter is found."""
    assert _should_skip_initial_section(
        is_front=False,
        word_count=80,
        found_chapter=False,
        skip_count=0,
    )


def test_should_not_skip_after_chapter_found() -> None:
    """Once chapter content starts, chunks should not be skipped."""
    assert not _should_skip_initial_section(
        is_front=True,
        word_count=50,
        found_chapter=True,
        skip_count=2,
    )


def test_find_content_start_returns_first_matching_line() -> None:
    """Should return index of first chapter-like line."""
    lines = [
        "Copyright notice",
        "Table of Contents",
        "Chapter 1",
        "Real content starts here",
    ]
    assert _find_content_start(lines) == 2


def test_find_content_start_returns_zero_when_no_match() -> None:
    """Should return zero when no chapter-like marker is found."""
    lines = [
        "Foreword",
        "Some intro text",
        "Another line",
    ]
    assert _find_content_start(lines) == 0
