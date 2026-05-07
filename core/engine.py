"""TTS backend engines and caching orchestration.

This module provides multiple TTS backends with automatic fallback:
1. Edge TTS (Microsoft Azure neural voices) - Primary, highest quality
2. gTTS (Google Text-to-Speech) - Secondary, good quality
3. eSpeak - Local synthesis, basic quality

Performance optimizations:
- Shared event loop for async Edge TTS operations
- Thread-safe event loop management
- Configurable timeouts for audio generation
"""

import asyncio
import hashlib
import importlib.util
import logging
import os
import shutil
import subprocess
import tempfile
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path

from .config import TTSConfig
from .constants import (
    CACHE_DIR,
    ESPEAK_SPEED_MAP,
    ESPEAK_VOICE_MAP,
    LANG_CONFIG,
    SPEED_MAP,
    TEMP_FILE_SUFFIX,
    WAV_SUFFIX,
)
from .logger import Logger

_log = logging.getLogger("tts")

# Performance: Timeout for audio generation (seconds)
AUDIO_GENERATION_TIMEOUT = 60

# Documented limit for text length
MAX_TEXT_LENGTH = 50000  # Maximum characters per TTS request

# Rate limiting defaults
_RATE_LIMIT_CALLS = 5
_RATE_LIMIT_WINDOW = 10.0


class _RateLimiter:
    """Simple sliding-window rate limiter for TTS API calls."""

    def __init__(self, max_calls: int = _RATE_LIMIT_CALLS, window: float = _RATE_LIMIT_WINDOW) -> None:
        self._max_calls = max_calls
        self._window = window
        self._timestamps: list[float] = []
        self._lock = threading.Lock()

    def acquire(self) -> None:
        """Block until an API call slot is available."""
        while True:
            with self._lock:
                now = time.monotonic()
                self._timestamps = [t for t in self._timestamps if now - t < self._window]
                if len(self._timestamps) < self._max_calls:
                    self._timestamps.append(now)
                    return
            time.sleep(0.5)


class TTSBackend(ABC):
    """Abstract base class for TTS engines."""

    def __init__(self, config: TTSConfig) -> None:
        """Initialize TTS backend.

        Args:
            config: TTS configuration with language and speed settings.
        """
        self.config = config
        self.voice = LANG_CONFIG[config.lang]["voice"]
        self.rate = SPEED_MAP[config.speed]

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is available for use."""
        ...

    @abstractmethod
    def generate_audio(self, text: str) -> bytes:
        """Generate audio data for the given text.

        Args:
            text: Text to convert to speech.

        Returns:
            Audio data as bytes.
        """
        ...

    def get_name(self) -> str:
        """Get the name of this backend."""
        return self.__class__.__name__


class EdgeTTSBackend(TTSBackend):
    """Microsoft Edge TTS backend using neural voices.

    Performance:
        Uses a shared event loop across all instances to avoid
        the overhead of creating a new event loop for each request.
    """

    # Shared event loop for async operations (class-level)
    _event_loop: asyncio.AbstractEventLoop | None = None
    _loop_lock = threading.Lock()
    _loop_thread: threading.Thread | None = None

    @classmethod
    def _get_event_loop(cls) -> asyncio.AbstractEventLoop:
        """Get or create shared event loop for Edge TTS operations.

        This avoids creating a new event loop for every audio generation
        request, which is expensive and can cause performance issues.

        Returns:
            Shared asyncio event loop running in a background thread.
        """
        if cls._event_loop is None or cls._event_loop.is_closed():
            with cls._loop_lock:
                # Double-check after acquiring lock
                if cls._event_loop is None or cls._event_loop.is_closed():
                    cls._event_loop = asyncio.new_event_loop()
                    cls._loop_thread = threading.Thread(
                        target=cls._event_loop.run_forever,
                        daemon=True,
                        name="EdgeTTS-EventLoop"
                    )
                    cls._loop_thread.start()
        return cls._event_loop

    @classmethod
    def _shutdown_event_loop(cls) -> None:
        """Shutdown the shared event loop (for cleanup)."""
        with cls._loop_lock:
            if cls._event_loop and not cls._event_loop.is_closed():
                cls._event_loop.call_soon_threadsafe(cls._event_loop.stop)
            if cls._loop_thread:
                cls._loop_thread.join(timeout=5)
            cls._event_loop = None
            cls._loop_thread = None

    def is_available(self) -> bool:
        """Check if edge-tts package is installed."""
        try:
            import edge_tts  # noqa: F401
            return True
        except ImportError:
            return False

    async def _generate_audio_async(self, text: str) -> bytes:
        """Generate audio asynchronously using Edge TTS.

        Args:
            text: Text to convert to speech.

        Returns:
            Audio data as bytes.

        Raises:
            RuntimeError: If audio stream is empty.
        """
        import edge_tts

        communicate = edge_tts.Communicate(text=text, voice=self.voice, rate=self.rate)
        audio_chunks: list[bytes] = []

        async for chunk in communicate.stream():
            if chunk.get("type") == "audio":
                data = chunk.get("data")
                if isinstance(data, bytes):
                    audio_chunks.append(data)

        if not audio_chunks:
            raise RuntimeError("Edge TTS returned empty audio stream")

        return b"".join(audio_chunks)

    def generate_audio(self, text: str) -> bytes:
        """Generate audio using shared event loop.

        This method submits the async audio generation task to the
        shared event loop running in a background thread, avoiding
        the overhead of creating a new event loop per request.

        Args:
            text: Text to convert to speech.

        Returns:
            Audio data as bytes.

        Raises:
            asyncio.TimeoutError: If generation exceeds timeout.
            RuntimeError: If audio generation fails.
        """
        loop = self._get_event_loop()
        future = asyncio.run_coroutine_threadsafe(
            self._generate_audio_async(text),
            loop
        )
        try:
            return future.result(timeout=AUDIO_GENERATION_TIMEOUT)
        except TimeoutError as e:
            raise TimeoutError(
                f"Edge TTS audio generation timed out after {AUDIO_GENERATION_TIMEOUT}s"
            ) from e


class GTTSBackend(TTSBackend):
    """Google Text-to-Speech backend.

    Note: This backend makes synchronous HTTP requests to Google's TTS API.
    For better performance, consider using EdgeTTSBackend which uses async I/O.
    """

    _available: bool | None = None

    def is_available(self) -> bool:
        """Check if gtts package is installed."""
        if GTTSBackend._available is not None:
            return GTTSBackend._available

        try:
            spec = importlib.util.find_spec("gtts")
            GTTSBackend._available = spec is not None
        except (ImportError, ValueError):
            GTTSBackend._available = False

        return GTTSBackend._available

    def generate_audio(self, text: str) -> bytes:
        """Generate audio using Google TTS.

        Args:
            text: Text to convert to speech.

        Returns:
            Audio data as bytes.

        Raises:
            RuntimeError: If gTTS fails to generate audio.
        """
        from gtts import gTTS

        tld = LANG_CONFIG[self.config.lang]["fallback_tld"]
        lang = "en" if "en" in self.config.lang else "ta"

        tts = gTTS(
            text=text,
            lang=lang,
            tld=tld or "com",
            slow=self.config.speed == "slow",
        )

        with tempfile.NamedTemporaryFile(suffix=TEMP_FILE_SUFFIX, delete=False) as temp_file:
            os.chmod(temp_file.name, 0o600)
            temp_path = temp_file.name

        try:
            tts.save(temp_path)
            return Path(temp_path).read_bytes()
        finally:
            Path(temp_path).unlink(missing_ok=True)


class EspeakBackend(TTSBackend):
    """eSpeak-ng backend for basic TTS.

    This backend uses the local eSpeak-ng synthesizer, which works
    offline but produces lower-quality robotic speech compared to
    neural TTS engines.
    """

    _binary_cache: str | None = None

    @classmethod
    def _find_binary(cls) -> str | None:
        """Find eSpeak binary path with caching."""
        if cls._binary_cache is not None:
            return cls._binary_cache if cls._binary_cache else None

        cls._binary_cache = shutil.which("espeak-ng") or shutil.which("espeak") or ""
        return cls._binary_cache if cls._binary_cache else None

    def is_available(self) -> bool:
        """Check if eSpeak binary is available."""
        return self._find_binary() is not None

    def generate_audio(self, text: str) -> bytes:
        """Generate audio using eSpeak-ng.

        Args:
            text: Text to convert to speech.

        Returns:
            WAV audio data as bytes.

        Raises:
            RuntimeError: If eSpeak binary not found or subprocess fails.
        """
        espeak_bin = self._find_binary()
        if not espeak_bin:
            raise RuntimeError("espeak binary not found")

        speed = ESPEAK_SPEED_MAP[self.config.speed]
        voice = ESPEAK_VOICE_MAP.get(self.config.lang, "en-us")

        with tempfile.NamedTemporaryFile(suffix=WAV_SUFFIX, delete=False) as temp_file:
            os.chmod(temp_file.name, 0o600)
            temp_path = temp_file.name

        try:
            subprocess.run(
                [espeak_bin, "-v", voice, "-s", speed, "-w", temp_path],
                input=text.encode(),
                capture_output=True,
                check=True,
                timeout=30,  # 30 second timeout for eSpeak
            )
            return Path(temp_path).read_bytes()
        except subprocess.TimeoutExpired as e:
            raise subprocess.TimeoutExpired(
                espeak_bin, 30,
                output=b"", stderr=b"eSpeak generation timed out"
            ) from e
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TTSEngine:
    """Main TTS engine with caching and backend fallback.

    This engine orchestrates text-to-speech synthesis with:
    - MD5-based caching to avoid regenerating audio
    - Automatic fallback through multiple backends
    - Text length validation and truncation

    Backend Priority:
        1. Edge TTS (Microsoft Azure neural voices) - Best quality
        2. gTTS (Google TTS) - Good quality, requires network
        3. eSpeak - Basic quality, works offline
    """

    BACKEND_CLASSES = [EdgeTTSBackend, GTTSBackend, EspeakBackend]
    _rate_limiter = _RateLimiter()

    def __init__(self, config: TTSConfig) -> None:
        """Initialize TTS engine.

        Args:
            config: TTS configuration for language, speed, and caching.
        """
        self.config = config
        self._backends: list[TTSBackend] | None = None

    @property
    def backends(self) -> list[TTSBackend]:
        """Get available backends, lazily initialized."""
        if self._backends is None:
            self._backends = []
            for backend_class in self.BACKEND_CLASSES:
                backend = backend_class(self.config)
                if backend.is_available():
                    self._backends.append(backend)
        return self._backends

    def generate(self, text: str) -> bytes | None:
        """Generate audio for text with caching and fallback.

        This method:
        1. Validates and optionally truncates text
        2. Checks cache for existing audio
        3. Tries each available backend until one succeeds
        4. Caches the result for future use

        Args:
            text: Text to convert to speech.

        Returns:
            Audio data as bytes, or None if all backends fail.
        """
        if not text or not text.strip():
            return None

        # Truncate excessively long text
        if len(text) > MAX_TEXT_LENGTH:
            text = text[:MAX_TEXT_LENGTH]
            Logger.log(f"Text truncated to {MAX_TEXT_LENGTH} chars", self.config)

        # Generate cache key from text + language + speed
        cache_key = hashlib.md5(
            f"{text}_{self.config.lang}_{self.config.speed}".encode()
        ).hexdigest()
        cache_file = CACHE_DIR / f"{cache_key}{TEMP_FILE_SUFFIX}"

        # Check cache first
        if self.config.cache_enabled and cache_file.exists():
            Logger.log("Cache hit", self.config)
            return cache_file.read_bytes()

        # Rate-limit API calls (not cache reads)
        self._rate_limiter.acquire()

        # Try each backend in priority order
        for backend in self.backends:
            try:
                data = backend.generate_audio(text)
                if self.config.cache_enabled:
                    cache_file.write_bytes(data)
                    from .runtime import CacheManager
                    CacheManager.enforce_limit()
                Logger.log(f"Generated with {backend.get_name()}", self.config)
                return data

            except (TimeoutError, subprocess.CalledProcessError, OSError, RuntimeError, subprocess.TimeoutExpired) as error:
                _log.warning("Backend %s failed: %s", backend.get_name(), error)
                continue

        # All backends failed
        return None

    @staticmethod
    def list_available_engines() -> dict[str, bool]:
        """List available TTS engines.

        Returns:
            Dictionary mapping engine names to availability status.
        """
        from .platform import detect_available_engines
        return detect_available_engines()
