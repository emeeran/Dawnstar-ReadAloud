"""Unit tests for custom exceptions module."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.exceptions import (
    TTSError,
    ConfigurationError,
    ExtractionError,
    EngineError,
    PlaybackError,
    IPCError,
    CacheError,
    SecurityError,
)


class TestTTSError:
    """Tests for base TTSError class."""

    def test_message_only(self):
        """Test error with message only."""
        error = TTSError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details is None

    def test_message_with_details(self):
        """Test error with message and details."""
        error = TTSError("Test error", details={"key": "value"})
        assert "Test error" in str(error)
        assert "key" in str(error)
        assert error.details == {"key": "value"}

    def test_details_string_conversion(self):
        """Test that details are included in string representation."""
        error = TTSError("Error", details="extra info")
        assert "extra info" in str(error)


class TestExceptionHierarchy:
    """Tests for exception inheritance."""

    def test_configuration_error_is_tts_error(self):
        """Test ConfigurationError inherits from TTSError."""
        error = ConfigurationError("config issue")
        assert isinstance(error, TTSError)
        assert isinstance(error, Exception)

    def test_extraction_error_is_tts_error(self):
        """Test ExtractionError inherits from TTSError."""
        error = ExtractionError("extraction failed")
        assert isinstance(error, TTSError)

    def test_engine_error_is_tts_error(self):
        """Test EngineError inherits from TTSError."""
        error = EngineError("engine failed")
        assert isinstance(error, TTSError)

    def test_playback_error_is_tts_error(self):
        """Test PlaybackError inherits from TTSError."""
        error = PlaybackError("playback failed")
        assert isinstance(error, TTSError)

    def test_ipc_error_is_tts_error(self):
        """Test IPCError inherits from TTSError."""
        error = IPCError("connection failed")
        assert isinstance(error, TTSError)

    def test_cache_error_is_tts_error(self):
        """Test CacheError inherits from TTSError."""
        error = CacheError("cache miss")
        assert isinstance(error, TTSError)

    def test_security_error_is_tts_error(self):
        """Test SecurityError inherits from TTSError."""
        error = SecurityError("unauthorized access")
        assert isinstance(error, TTSError)

    def test_all_exceptions_can_be_raised(self):
        """Test all exception types can be raised and caught."""
        exceptions = [
            ConfigurationError,
            ExtractionError,
            EngineError,
            PlaybackError,
            IPCError,
            CacheError,
            SecurityError,
        ]

        for exc_class in exceptions:
            try:
                raise exc_class("test")
            except TTSError as e:
                assert e.message == "test"


class TestExceptionUsage:
    """Tests for practical exception usage patterns."""

    def test_catch_specific_then_general(self):
        """Test catching specific exception before general."""
        with pytest.raises(EngineError):
            try:
                raise EngineError("specific error")
            except ExtractionError:
                pass
            except TTSError:
                raise

    def test_exception_chaining(self):
        """Test exception can be chained."""
        try:
            try:
                raise ValueError("original")
            except ValueError as e:
                raise EngineError("wrapped") from e
        except EngineError as e:
            assert e.__cause__ is not None
            assert isinstance(e.__cause__, ValueError)


import pytest
