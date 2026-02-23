"""Custom exception hierarchy for the TTS application.

This module defines a structured exception system that provides:
- Clear error categorization
- Consistent error handling patterns
- Better debugging information
"""

from typing import Any, Optional


class TTSError(Exception):
    """Base exception for all TTS-related errors.

    Attributes:
        message: Human-readable error description.
        details: Optional additional context for debugging.
    """

    def __init__(self, message: str, details: Optional[Any] = None) -> None:
        """Initialize TTS error.

        Args:
            message: Human-readable error description.
            details: Optional additional context for debugging.
        """
        self.message = message
        self.details = details
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (details: {self.details})"
        return self.message


class ConfigurationError(TTSError):
    """Raised when configuration is invalid or cannot be loaded.

    Examples:
        - Missing required configuration file
        - Invalid configuration values
        - YAML parsing errors
    """
    pass


class ExtractionError(TTSError):
    """Raised when content extraction fails.

    Examples:
        - File not found
        - Unsupported file format
        - PDF/EPUB parsing errors
        - URL fetch failures
    """
    pass


class EngineError(TTSError):
    """Raised when TTS engine operation fails.

    Examples:
        - No available TTS backends
        - Backend initialization failure
        - Audio generation failure
        - Network errors during TTS API calls
    """
    pass


class PlaybackError(TTSError):
    """Raised when audio playback fails.

    Examples:
        - No audio player available
        - Playback subprocess errors
        - Audio device errors
    """
    pass


class IPCError(TTSError):
    """Raised when IPC communication fails.

    Examples:
        - Daemon not running
        - Socket connection errors
        - Message parsing errors
        - Command timeout
    """
    pass


class CacheError(TTSError):
    """Raised when cache operations fail.

    Examples:
        - Cache directory creation failure
        - Cache file read/write errors
        - Cache eviction errors
    """
    pass


class SecurityError(TTSError):
    """Raised when security constraints are violated.

    Examples:
        - Path traversal attempts
        - Unauthorized file access
        - Invalid input sanitization
    """
    pass
