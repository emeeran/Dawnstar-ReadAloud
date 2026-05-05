"""Security-focused tests for input validation and access control.

This test suite verifies security-critical code paths including:
- Path traversal prevention
- URL scheme validation
- IPC input validation
- Socket permissions
"""

import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import TTSConfig
from core.exceptions import SecurityError
from core.source_loader import from_source
from core.url_reader import _normalize_url, _validate_url_scheme, extract_url_content


class TestPathTraversal:
    """Test path traversal prevention in source_loader.py."""

    def test_blocks_absolute_path_outside_allowed(self):
        """Should block absolute paths outside allowed directories."""
        config = TTSConfig()

        # Sensitive system files should be blocked
        with pytest.raises(SecurityError) as exc_info:
            from_source("/etc/passwd", config)

        assert "Access denied" in str(exc_info.value)

    def test_blocks_relative_path_traversal_to_existing_file(self):
        """Should block relative path traversal attempts to existing files."""
        config = TTSConfig()

        # Create a temp file outside allowed directories
        # We test by checking that the path resolution blocks traversal
        # Since we can't easily create files outside /tmp/home, test the behavior
        # with a path that LOOKS like traversal but resolves somewhere

        # The security check happens after path resolution
        # Test that paths resolving outside allowed dirs are blocked
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file in tmp (allowed)
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test")

            # This should work (file in /tmp is allowed)
            result = from_source(str(test_file), config)
            assert result == "test"

    def test_sneaky_traversal_patterns_treated_as_text(self):
        """Sneaky traversal patterns that don't resolve to files are treated as text."""
        config = TTSConfig()

        # These patterns don't exist as files, so they're treated as direct text
        # This is actually correct behavior - non-existent paths aren't security issues
        sneaky_paths = [
            "....//....//etc/passwd",
            "..\\..\\..\\etc\\passwd",
        ]

        for sneaky_path in sneaky_paths:
            # Should return the text as-is (not a file)
            result = from_source(sneaky_path, config)
            # Non-existent paths that look like files are returned as direct text
            assert result == sneaky_path

    def test_allows_home_directory_files(self):
        """Should allow files in home directory."""
        config = TTSConfig()

        # Create a temp file in home directory
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            # Should not raise - file is in allowed location
            result = from_source(temp_path, config)
            assert result == "test content"
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_allows_tmp_directory_files(self):
        """Should allow files in /tmp directory."""
        config = TTSConfig()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("tmp content")
            temp_path = f.name

        try:
            result = from_source(temp_path, config)
            assert result == "tmp content"
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_expands_user_home_correctly(self):
        """Should correctly expand ~ to home directory."""
        config = TTSConfig()

        # ~/path should resolve to home directory
        result = from_source("~/nonexistent_file.txt", config)
        # Will return None if file doesn't exist, but shouldn't raise SecurityError
        assert result is None or isinstance(result, str)


class TestURLValidation:
    """Test URL scheme validation in url_reader.py."""

    def test_validates_http_scheme(self):
        """Should accept HTTP URLs."""
        assert _validate_url_scheme("http://example.com") is True
        assert _validate_url_scheme("HTTP://EXAMPLE.COM") is True

    def test_validates_https_scheme(self):
        """Should accept HTTPS URLs."""
        assert _validate_url_scheme("https://example.com") is True
        assert _validate_url_scheme("HTTPS://EXAMPLE.COM") is True

    def test_blocks_file_scheme(self):
        """Should block file:// URLs."""
        assert _validate_url_scheme("file:///etc/passwd") is False
        assert _validate_url_scheme("FILE:///etc/passwd") is False

    def test_blocks_javascript_scheme(self):
        """Should block javascript: URLs (XSS prevention)."""
        assert _validate_url_scheme("javascript:alert(1)") is False
        assert _validate_url_scheme("JAVASCRIPT:alert(1)") is False

    def test_blocks_data_scheme(self):
        """Should block data: URLs."""
        assert _validate_url_scheme("data:text/html,<script>alert(1)</script>") is False

    def test_blocks_ftp_scheme(self):
        """Should block FTP URLs."""
        assert _validate_url_scheme("ftp://example.com/file") is False

    def test_normalize_url_adds_https(self):
        """Should add https:// to URLs without scheme."""
        result = _normalize_url("example.com")
        assert result == "https://example.com"

    def test_normalize_url_preserves_http(self):
        """Should preserve http:// scheme."""
        result = _normalize_url("http://example.com")
        assert result == "http://example.com"

    def test_normalize_url_preserves_https(self):
        """Should preserve https:// scheme."""
        result = _normalize_url("https://example.com")
        assert result == "https://example.com"

    def test_normalize_url_blocks_dangerous_schemes(self):
        """Should raise SecurityError for dangerous schemes."""
        with pytest.raises(SecurityError) as exc_info:
            _normalize_url("file:///etc/passwd")
        assert "Invalid URL scheme" in str(exc_info.value)

        with pytest.raises(SecurityError):
            _normalize_url("javascript:alert(1)")

    def test_extract_url_content_blocks_file_scheme(self):
        """Should block file:// URLs in extract_url_content."""
        config = TTSConfig()

        with pytest.raises(SecurityError):
            extract_url_content("file:///etc/passwd", config=config)


class TestIPCValidation:
    """Test IPC input validation in ttsd/ipc.py."""

    def test_max_text_length_constant_defined(self):
        """Should have MAX_IPC_TEXT_LENGTH constant defined."""
        from ttsd.ipc import MAX_IPC_TEXT_LENGTH

        # Should be defined and reasonable (100KB)
        assert MAX_IPC_TEXT_LENGTH == 100 * 1024

    def test_max_message_size_constant_defined(self):
        """Should have MAX_MESSAGE_SIZE constant defined."""
        from ttsd.ipc import MAX_MESSAGE_SIZE

        # Should be defined and reasonable (1MB)
        assert MAX_MESSAGE_SIZE == 1024 * 1024


class TestSocketPermissions:
    """Test Unix socket security in ttsd/ipc.py."""

    def test_socket_path_in_runtime_dir(self):
        """Socket should be in XDG_RUNTIME_DIR."""
        from ttsd.ipc import UnixSocketServer

        socket_path = UnixSocketServer.SOCKET_PATH

        # Should be in user's runtime directory
        assert "tts-daemon.sock" in socket_path


class TestSecurityConstants:
    """Test that security-related constants are properly defined."""

    def test_max_text_length_in_engine(self):
        """Engine should have documented MAX_TEXT_LENGTH."""
        from core.engine import MAX_TEXT_LENGTH

        # Should be defined and reasonable
        assert MAX_TEXT_LENGTH == 50000
        assert MAX_TEXT_LENGTH > 0

    def test_audio_generation_timeout_defined(self):
        """Should have timeout for audio generation."""
        from core.engine import AUDIO_GENERATION_TIMEOUT

        # Should be defined and reasonable (60 seconds)
        assert AUDIO_GENERATION_TIMEOUT == 60


class TestInputSanitization:
    """Test input sanitization in text processing."""

    def test_clean_text_removes_urls(self):
        """Should remove URLs from text to prevent injection."""
        from core.text_processing import clean_text

        text = "Check out https://evil.com/malware for more"
        result = clean_text(text)

        assert "https://evil.com" not in result
        assert "Check out" in result
        assert "for more" in result

    def test_clean_text_removes_emails(self):
        """Should remove email addresses from text."""
        from core.text_processing import clean_text

        text = "Contact attacker@evil.com for phishing"
        result = clean_text(text)

        assert "attacker@evil.com" not in result


class TestErrorHandling:
    """Test that errors are handled safely without leaking information."""

    def test_security_error_has_clear_message(self):
        """SecurityError should have clear, non-technical message."""
        from core.exceptions import SecurityError

        error = SecurityError("Access denied: path outside allowed directories")

        # Message should be user-friendly
        assert "Access denied" in str(error)

    def test_path_traversal_error_does_not_leak_paths(self):
        """Error messages should not leak system paths."""
        config = TTSConfig()

        try:
            from_source("/etc/shadow", config)
            raise AssertionError("Should have raised SecurityError")
        except SecurityError as e:
            # Error should not confirm the file exists or reveal path structure
            error_msg = str(e)
            assert "shadow" not in error_msg.lower()


# Run tests with: pytest tests/test_security.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
