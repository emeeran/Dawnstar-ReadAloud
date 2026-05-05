"""TTS backend engines and caching orchestration."""

import asyncio
import hashlib
import importlib.util
import shutil
import subprocess
import tempfile
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


class TTSBackend(ABC):
    """Abstract base class for TTS engines."""

    def __init__(self, config: TTSConfig) -> None:
        self.config = config
        self.voice = LANG_CONFIG[config.lang]["voice"]
        self.rate = SPEED_MAP[config.speed]

    @abstractmethod
    def is_available(self) -> bool:
        ...

    @abstractmethod
    def generate_audio(self, text: str) -> bytes:
        ...

    def get_name(self) -> str:
        return self.__class__.__name__


class EdgeTTSBackend(TTSBackend):
    """Microsoft Edge TTS backend using neural voices."""

    def is_available(self) -> bool:
        try:
            import edge_tts  # noqa: F401

            return True
        except ImportError:
            return False

    async def _generate_audio_async(self, text: str) -> bytes:
        import edge_tts

        communicate = edge_tts.Communicate(text=text, voice=self.voice, rate=self.rate)
        audio_chunks: list[bytes] = []

        async for chunk in communicate.stream():
            if chunk.get("type") == "audio":
                data = chunk.get("data")
                if isinstance(data, bytes):
                    audio_chunks.append(data)

        return b"".join(audio_chunks)

    def generate_audio(self, text: str) -> bytes:
        return asyncio.run(self._generate_audio_async(text))


class GTTSBackend(TTSBackend):
    """Google Text-to-Speech backend."""

    _available: bool | None = None

    def is_available(self) -> bool:
        if GTTSBackend._available is not None:
            return GTTSBackend._available

        try:
            spec = importlib.util.find_spec("gtts")
            GTTSBackend._available = spec is not None
        except (ImportError, ValueError):
            GTTSBackend._available = False

        return GTTSBackend._available

    def generate_audio(self, text: str) -> bytes:
        from gtts import gTTS

        tld = LANG_CONFIG[self.config.lang]["fallback_tld"]
        lang = "en" if "en" in self.config.lang else "ta"

        tts = gTTS(
            text=text,
            lang=lang,
            tld=tld or "com",
            slow=self.config.speed == "slow",
        )

        with tempfile.NamedTemporaryFile(suffix=TEMP_FILE_SUFFIX) as temp_file:
            tts.save(temp_file.name)
            return Path(temp_file.name).read_bytes()


class EspeakBackend(TTSBackend):
    """eSpeak-ng backend for basic TTS."""

    _binary_cache: str | None = None

    @classmethod
    def _find_binary(cls) -> str | None:
        if cls._binary_cache is not None:
            return cls._binary_cache if cls._binary_cache else None

        cls._binary_cache = shutil.which("espeak-ng") or shutil.which("espeak") or ""
        return cls._binary_cache if cls._binary_cache else None

    def is_available(self) -> bool:
        return self._find_binary() is not None

    def generate_audio(self, text: str) -> bytes:
        espeak_bin = self._find_binary()
        if not espeak_bin:
            raise RuntimeError("espeak binary not found")

        speed = ESPEAK_SPEED_MAP[self.config.speed]
        voice = ESPEAK_VOICE_MAP.get(self.config.lang, "en-us")

        with tempfile.NamedTemporaryFile(suffix=WAV_SUFFIX, delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            subprocess.run(
                [espeak_bin, "-v", voice, "-s", speed, "-w", temp_path],
                input=text.encode(),
                capture_output=True,
                check=True,
            )
            return Path(temp_path).read_bytes()
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TTSEngine:
    """Main TTS engine with caching and backend fallback."""

    BACKEND_CLASSES = [EdgeTTSBackend, GTTSBackend, EspeakBackend]

    MAX_TEXT_LENGTH = 50000

    def __init__(self, config: TTSConfig) -> None:
        self.config = config
        self._backends: list[TTSBackend] | None = None

    @property
    def backends(self) -> list[TTSBackend]:
        if self._backends is None:
            self._backends = []
            for backend_class in self.BACKEND_CLASSES:
                backend = backend_class(self.config)
                if backend.is_available():
                    self._backends.append(backend)
        return self._backends

    def generate(self, text: str) -> bytes | None:
        if not text or not text.strip():
            return None

        if len(text) > self.MAX_TEXT_LENGTH:
            text = text[:self.MAX_TEXT_LENGTH]
            Logger.log(f"Text truncated to {self.MAX_TEXT_LENGTH} chars", self.config)

        cache_key = hashlib.md5(
            f"{text}_{self.config.lang}_{self.config.speed}".encode()
        ).hexdigest()
        cache_file = CACHE_DIR / f"{cache_key}{TEMP_FILE_SUFFIX}"

        if self.config.cache_enabled and cache_file.exists():
            Logger.log("Cache hit", self.config)
            return cache_file.read_bytes()

        for backend in self.backends:
            try:
                data = backend.generate_audio(text)
                if self.config.cache_enabled:
                    cache_file.write_bytes(data)
                Logger.log(f"Generated with {backend.get_name()}", self.config)
                return data
            except (subprocess.CalledProcessError, OSError, RuntimeError, subprocess.TimeoutExpired) as error:
                if self.config.verbose:
                    print(f"  Backend {backend.get_name()} failed: {error}")
                continue

        return None

    @staticmethod
    def list_available_engines() -> dict[str, bool]:
        edge_available = EdgeTTSBackend(TTSConfig()).is_available()
        return {
            "edge": edge_available,
            "gtts": True,
            "espeak": shutil.which("espeak-ng") is not None or shutil.which("espeak") is not None,
        }
