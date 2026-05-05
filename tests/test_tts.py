"""Unit tests for TTS application."""
# Import modules to test
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import (
    CHUNK_SIZE,
    LANG_CONFIG,
    SPEED_MAP,
    CacheManager,
    ContentExtractor,
    NotificationManager,
    TTSConfig,
    TTSEngine,
)
from app_config import TTSAppConfig


class TestContentExtractor:
    """Tests for ContentExtractor class."""

    def test_clean_text_removes_urls(self):
        """Test that URLs are removed from text."""
        text = "Visit https://example.com for more info"
        result = ContentExtractor.clean_text(text)
        assert "https://example.com" not in result
        assert "Visit" in result
        assert "for more info" in result

    def test_clean_text_removes_emails(self):
        """Test that email addresses are removed."""
        text = "Contact user@example.com for help"
        result = ContentExtractor.clean_text(text)
        assert "user@example.com" not in result
        assert "Contact" in result
        assert "for help" in result

    def test_clean_text_strips_whitespace(self):
        """Test that leading/trailing whitespace is removed."""
        text = "  hello world  "
        result = ContentExtractor.clean_text(text)
        assert result == "hello world"

    def test_clean_text_strips_markdown_headers(self):
        """Test that Markdown headers are stripped."""
        text = "# Header 1\n## Header 2\nContent"
        result = ContentExtractor.clean_text(text)
        assert "Header 1" in result
        assert "Header 2" in result
        assert "#" not in result

    def test_clean_text_strips_markdown_links(self):
        """Test that Markdown links are converted to text."""
        text = "Check out [Gemini](https://gemini.google.com)"
        result = ContentExtractor.clean_text(text)
        assert "Gemini" in result
        assert "https://gemini.google.com" not in result
        assert "[" not in result

    def test_clean_text_strips_markdown_emphasis(self):
        """Test that bold and italic markers are removed."""
        text = "**Bold** and *Italic* text"
        result = ContentExtractor.clean_text(text)
        assert result == "Bold and Italic text"

    def test_chunk_text_short_text(self):
        """Test that short text returns single chunk."""
        text = "Hello world"
        chunks = ContentExtractor.chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0] == "Hello world"

    def test_chunk_text_respects_sentence_boundaries(self):
        """Test that chunks split at natural boundaries."""
        text = "First sentence. Second sentence. Third sentence."
        chunks = ContentExtractor.chunk_text(text, size=25)
        assert len(chunks) >= 2
        # Verify all original content is preserved
        combined = " ".join(chunks)
        assert "First sentence" in combined
        assert "Second sentence" in combined
        assert "Third sentence" in combined

    def test_chunk_text_empty_returns_empty(self):
        """Test that empty text returns empty list."""
        chunks = ContentExtractor.chunk_text("")
        assert chunks == []

        chunks = ContentExtractor.chunk_text("   ")
        assert chunks == []

    def test_from_source_stdin_marker(self):
        """Test stdin marker returns None when no stdin."""
        config = TTSConfig()
        # When source is "-", it tries to read stdin
        # This test verifies the path is taken
        with patch("sys.stdin.read", return_value="test input"):
            result = ContentExtractor.from_source("-", config)
            assert result == "test input"

    def test_from_source_direct_text(self):
        """Test that direct text is returned as-is."""
        config = TTSConfig()
        result = ContentExtractor.from_source("Hello world", config)
        assert result == "Hello world"


class TestTTSConfig:
    """Tests for TTSConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = TTSConfig()
        assert config.lang == "en-us"
        assert config.cache_enabled is True
        assert config.verbose is False
        assert config.speed == "normal"

    def test_lang_alias_normalization(self):
        """Test language aliases are normalized."""
        config = TTSConfig(lang="en")
        assert config.lang == "en-us"

        config = TTSConfig(lang="en-gb")
        assert config.lang == "en-uk"

    def test_custom_values(self):
        """Test custom configuration values."""
        config = TTSConfig(lang="ta", speed="fast", verbose=True)
        assert config.lang == "ta"
        assert config.speed == "fast"
        assert config.verbose is True


class TestCacheManager:
    """Tests for CacheManager class."""

    def test_get_cache_stats_empty(self):
        """Test cache stats when cache is empty."""
        stats = CacheManager.get_cache_stats()
        assert "files" in stats
        assert "size_mb" in stats
        assert "max_size_mb" in stats

    def test_initialize_sets_max_size(self):
        """Test that initialize sets max size."""
        CacheManager.initialize(max_size_mb=100)
        assert CacheManager._max_size_bytes == 100 * 1024 * 1024


class TestNotificationManager:
    """Tests for NotificationManager class."""

    def test_set_enabled(self):
        """Test enabling/disabling notifications."""
        NotificationManager.set_enabled(True)
        assert NotificationManager._enabled is True

        NotificationManager.set_enabled(False)
        assert NotificationManager._enabled is False

        # Reset to enabled for other tests
        NotificationManager.set_enabled(True)

    @patch("shutil.which")
    def test_is_available(self, mock_which):
        """Test notification availability check."""
        mock_which.return_value = "/usr/bin/notify-send"
        NotificationManager._available = None  # Reset cache
        assert NotificationManager.is_available() is True

        mock_which.return_value = None
        NotificationManager._available = None  # Reset cache
        assert NotificationManager.is_available() is False


class TestTTSEngine:
    """Tests for TTSEngine class."""

    def test_list_available_engines(self):
        """Test engine listing returns dict."""
        engines = TTSEngine.list_available_engines()
        assert isinstance(engines, dict)
        assert "edge" in engines
        assert "gtts" in engines
        assert "espeak" in engines

    def test_backend_property_lazy_loads(self):
        """Test that backends are lazily loaded."""
        config = TTSConfig()
        engine = TTSEngine(config)
        assert engine._backends is None
        backends = engine.backends
        assert engine._backends is not None
        assert isinstance(backends, list)


class TestConstants:
    """Tests for module constants."""

    def test_lang_config_has_required_keys(self):
        """Test language config has all required keys."""
        for lang in ["en-us", "en-uk", "ta"]:
            assert lang in LANG_CONFIG
            assert "name" in LANG_CONFIG[lang]
            assert "voice" in LANG_CONFIG[lang]

    def test_speed_map_values(self):
        """Test speed map has correct values."""
        assert SPEED_MAP["slow"] == "-25%"
        assert SPEED_MAP["normal"] == "+0%"
        assert SPEED_MAP["fast"] == "+25%"

    def test_chunk_size_reasonable(self):
        """Test chunk size is reasonable."""
        assert 100 <= CHUNK_SIZE <= 2000


class TestTTSAppConfig:
    """Tests for application configuration."""

    def test_defaults(self):
        """Test default configuration values."""
        config = TTSAppConfig()
        assert config.language == "en-us"
        assert config.speed == "normal"
        assert config.cache_enabled is True
        assert config.verbose is False

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = TTSAppConfig(language="ta", speed="fast")
        d = config.to_dict()
        assert d["language"] == "ta"
        assert d["speed"] == "fast"

    def test_get_config_path(self):
        """Test config path is returned."""
        path = TTSAppConfig.get_config_path()
        assert ".config/tts/config.yaml" in str(path)


# Run tests with: pytest tests/test_tts.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
