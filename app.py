#!/usr/bin/env python3
"""Enhanced Text-to-Speech Application."""
import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import tts_platform

# Constants
CACHE_DIR = Path.home() / ".cache" / "tts_app"
CHUNK_SIZE = 500
DEFAULT_LANG = "en-us"
TEMP_FILE_SUFFIX = ".mp3"
WAV_SUFFIX = ".wav"

# Configuration
LANG_CONFIG: Dict[str, Dict[str, Optional[str]]] = {
    "en-us": {"name": "English (US)", "voice": "en-US-GuyNeural", "fallback_tld": "us"},
    "en-uk": {"name": "English (UK)", "voice": "en-GB-RyanNeural", "fallback_tld": "co.uk"},
    "ta": {"name": "Tamil", "voice": "ta-IN-ValluvarNeural", "fallback_tld": None},
}

LANG_ALIASES = {"en": "en-us", "en-gb": "en-uk"}

SPEED_MAP = {"slow": "-25%", "normal": "+0%", "fast": "+25%"}

ESPEAK_SPEED_MAP = {"slow": "120", "normal": "160", "fast": "200"}

ESPEAK_VOICE_MAP = {"en-us": "en-us", "en-uk": "en-uk", "ta": "ta-in"}

SENTENCE_BREAK_CHARS = [". ", "! ", "? ", "; ", ": ", ", ", " "]


def find_edge_tts_binary() -> Optional[str]:
    """Find edge-tts binary in venv or system PATH."""
    script_dir = Path(__file__).parent
    search_paths = [
        script_dir / "venv" / "bin" / "edge-tts",
        script_dir / ".venv" / "bin" / "edge-tts",
        Path(sys.executable).parent / "edge-tts",
    ]
    for path in search_paths:
        if path.exists():
            return str(path)
    return shutil.which("edge-tts")


@dataclass
class TTSConfig:
    """TTS configuration settings."""

    lang: str = DEFAULT_LANG
    cache_enabled: bool = True
    verbose: bool = False
    speed: str = "normal"
    engine: Optional[str] = None

    def __post_init__(self) -> None:
        """Normalize language code and ensure cache directory exists."""
        if self.lang not in LANG_CONFIG:
            self.lang = LANG_ALIASES.get(self.lang, DEFAULT_LANG)
        if self.cache_enabled:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)


class Logger:
    """Simple verbose logger."""

    @staticmethod
    def log(msg: str, config: TTSConfig) -> None:
        """Log message if verbose mode is enabled."""
        if config.verbose:
            print(f"✓ {msg}")

    @staticmethod
    def error(msg: str) -> None:
        """Log error message."""
        print(f"✗ {msg}")


class ContentExtractor:
    """Extract and process text content from various sources."""

    @staticmethod
    def clean_text(text: str) -> str:
        """Remove URLs, emails, and normalize whitespace."""
        text = re.sub(r"http[s]?://\S+", "", text)
        text = re.sub(r"\S+@\S+", "", text)
        return text.strip()

    @staticmethod
    def chunk_text(text: str, size: int = CHUNK_SIZE) -> List[str]:
        """Split text into chunks at natural sentence boundaries."""
        if len(text) <= size:
            return [text] if text.strip() else []

        chunks: List[str] = []
        pos = 0

        while pos < len(text):
            end = min(pos + size, len(text))
            chunk = text[pos:end]

            # Find best break point
            for char in SENTENCE_BREAK_CHARS:
                break_pt = chunk.rfind(char)
                if break_pt != -1:
                    end = pos + break_pt + 1
                    break

            clean_chunk = text[pos:end].strip()
            if clean_chunk:
                chunks.append(clean_chunk)
            pos = end

        return chunks

    @classmethod
    def from_source(cls, source: str, config: TTSConfig) -> Optional[str]:
        """Extract text from file, stdin, or direct input."""
        if source == "-":
            return sys.stdin.read()

        source = source.strip().strip("'").strip('"')

        if os.path.exists(source):
            try:
                return Path(source).read_text(encoding="utf-8", errors="ignore")
            except OSError as e:
                Logger.log(f"Read error: {e}", config)
                return None

        return source


class AudioPlayer:
    """Auto-detecting audio player for MP3/WAV playback."""

    _player_cmd: Optional[List[str]] = None

    # Player candidates in priority order (name, arguments)
    PLAYER_CANDIDATES = [
        ("mpg123", ["-q"]),
        ("paplay", []),
        ("cvlc", ["--play-and-exit", "--no-video", "--quiet"]),
        ("ffplay", ["-nodisp", "-autoexit", "-loglevel", "quiet"]),
    ]

    @classmethod
    def get_player(cls) -> Optional[List[str]]:
        """Find available audio player."""
        if cls._player_cmd:
            return cls._player_cmd

        for bin_name, args in cls.PLAYER_CANDIDATES:
            if shutil.which(bin_name):
                cls._player_cmd = [bin_name] + args
                return cls._player_cmd

        return None

    @classmethod
    def play(cls, audio_data: bytes, config: TTSConfig) -> bool:
        """Play audio data using detected player."""
        cmd = cls.get_player()
        if not cmd:
            Logger.error("No audio player found")
            return False

        with tempfile.NamedTemporaryFile(suffix=TEMP_FILE_SUFFIX, delete=False) as tf:
            tf.write(audio_data)
            tf.flush()
            temp_path = tf.name

        try:
            subprocess.run(cmd + [temp_path], check=True, timeout=300)
            return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"Playback error: {e}")
            if e.stderr:
                print(f"  stderr: {e.stderr.decode()}")
            return False
        except subprocess.TimeoutExpired:
            Logger.error("Playback timeout")
            return False
        except OSError as e:
            Logger.error(f"Playback error: {e}")
            return False
        finally:
            os.unlink(temp_path)


class TTSBackend(ABC):
    """Abstract base class for TTS engines."""

    def __init__(self, config: TTSConfig) -> None:
        self.config = config
        self.voice = LANG_CONFIG[config.lang]["voice"]
        self.rate = SPEED_MAP[config.speed]

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is available."""
        pass

    @abstractmethod
    def generate_audio(self, text: str) -> bytes:
        """Generate audio data for text."""
        pass

    def get_name(self) -> str:
        """Return backend name for logging."""
        return self.__class__.__name__


class EdgeTTSBackend(TTSBackend):
    """Microsoft Edge TTS backend using neural voices."""

    def is_available(self) -> bool:
        return find_edge_tts_binary() is not None

    def generate_audio(self, text: str) -> bytes:
        edge_bin = find_edge_tts_binary()
        if not edge_bin:
            raise RuntimeError("edge-tts binary not found")

        with tempfile.NamedTemporaryFile(suffix=TEMP_FILE_SUFFIX) as tf:
            subprocess.run(
                [edge_bin, "--voice", self.voice, "--rate", self.rate,
                 "--text", text, "--write-media", tf.name],
                check=True,
                capture_output=True
            )
            return Path(tf.name).read_bytes()


class GTTSBackend(TTSBackend):
    """Google Text-to-Speech backend."""

    def is_available(self) -> bool:
        try:
            import gtts  # noqa: F401
            return True
        except ImportError:
            return False

    def generate_audio(self, text: str) -> bytes:
        from gtts import gTTS

        tld = LANG_CONFIG[self.config.lang]["fallback_tld"]
        lang = "en" if "en" in self.config.lang else "ta"

        tts = gTTS(
            text=text,
            lang=lang,
            tld=tld or "com",
            slow=self.config.speed == "slow"
        )

        with tempfile.NamedTemporaryFile(suffix=TEMP_FILE_SUFFIX) as tf:
            tts.save(tf.name)
            return Path(tf.name).read_bytes()


class EspeakBackend(TTSBackend):
    """eSpeak-ng backend for basic TTS."""

    def is_available(self) -> bool:
        return shutil.which("espeak-ng") is not None or shutil.which("espeak") is not None

    def generate_audio(self, text: str) -> bytes:
        espeak_bin = shutil.which("espeak-ng") or shutil.which("espeak")
        if not espeak_bin:
            raise RuntimeError("espeak binary not found")

        speed = ESPEAK_SPEED_MAP[self.config.speed]
        voice = ESPEAK_VOICE_MAP.get(self.config.lang, "en-us")

        with tempfile.NamedTemporaryFile(suffix=WAV_SUFFIX, delete=False) as tf:
            temp_path = tf.name

        try:
            subprocess.run(
                [espeak_bin, "-v", voice, "-s", speed, "-w", temp_path],
                input=text.encode(),
                capture_output=True,
                check=True
            )
            return Path(temp_path).read_bytes()
        finally:
            os.unlink(temp_path)


class TTSEngine:
    """Main TTS engine with caching and backend fallback."""

    BACKEND_CLASSES = [EdgeTTSBackend, GTTSBackend, EspeakBackend]

    def __init__(self, config: TTSConfig) -> None:
        self.config = config
        self._backends: Optional[List[TTSBackend]] = None

    @property
    def backends(self) -> List[TTSBackend]:
        """Get list of available backends."""
        if self._backends is None:
            self._backends = []
            for backend_class in self.BACKEND_CLASSES:
                backend = backend_class(self.config)
                if backend.is_available():
                    self._backends.append(backend)
        return self._backends

    def generate(self, text: str) -> Optional[bytes]:
        """Generate audio for text, using cache if available."""
        cache_key = hashlib.md5(
            f"{text}_{self.config.lang}_{self.config.speed}".encode()
        ).hexdigest()
        cache_file = CACHE_DIR / f"{cache_key}{TEMP_FILE_SUFFIX}"

        # Check cache
        if self.config.cache_enabled and cache_file.exists():
            Logger.log("Cache hit", self.config)
            return cache_file.read_bytes()

        # Try each backend
        for backend in self.backends:
            try:
                data = backend.generate_audio(text)
                if self.config.cache_enabled:
                    cache_file.write_bytes(data)
                Logger.log(f"Generated with {backend.get_name()}", self.config)
                return data
            except (subprocess.CalledProcessError, OSError, RuntimeError):
                continue

        return None

    @staticmethod
    def list_available_engines() -> Dict[str, bool]:
        """Check availability of each TTS engine."""
        return {
            "edge": find_edge_tts_binary() is not None,
            "gtts": True,
            "espeak": shutil.which("espeak-ng") is not None
            or shutil.which("espeak") is not None,
        }


class CLI:
    """Command-line interface handler."""

    def __init__(self) -> None:
        self.args = self._parse_args()
        self.config = TTSConfig(
            lang=self.args.lang,
            cache_enabled=not self.args.no_cache,
            verbose=self.args.verbose,
            speed=self.args.speed,
        )

    @staticmethod
    def _parse_args() -> argparse.Namespace:
        """Parse command-line arguments."""
        parser = argparse.ArgumentParser(description="Lightweight Neural TTS")
        parser.add_argument("source", nargs="*")
        parser.add_argument("-l", "--lang", default=DEFAULT_LANG)
        parser.add_argument(
            "-s", "--speed",
            default="normal",
            choices=["slow", "normal", "fast"]
        )
        parser.add_argument("-v", "--verbose", action="store_true")
        parser.add_argument("--no-cache", action="store_true")
        parser.add_argument("--clear-cache", action="store_true")
        parser.add_argument("--list-engines", action="store_true")
        parser.add_argument(
            "--get-clipboard",
            action="store_true",
            help="Print clipboard text and exit"
        )
        return parser.parse_args()

    def handle_get_clipboard(self) -> int:
        """Handle --get-clipboard flag."""
        text = tts_platform.get_clipboard_text()
        if text:
            print(text)
            return 0
        return 1

    def handle_list_engines(self) -> int:
        """Handle --list-engines flag."""
        engines = TTSEngine.list_available_engines()
        print("Available TTS engines:")
        for name, available in engines.items():
            status = "✓" if available else "✗"
            print(f"  {status} {name}")
        return 0

    def handle_clear_cache(self) -> int:
        """Handle --clear-cache flag."""
        if CACHE_DIR.exists():
            shutil.rmtree(CACHE_DIR)
        print("Done.")
        return 0

    def run_interactive(self) -> int:
        """Run interactive mode."""
        print("Interactive mode - 'quit' to exit")
        tts = TTSEngine(self.config)

        while True:
            try:
                text = input("> ")
            except EOFError:
                break

            if text.lower() == "quit":
                break

            if text:
                self._speak_text(text, tts)

        return 0

    def _speak_text(self, text: str, tts: TTSEngine) -> bool:
        """Clean, chunk, and speak text."""
        clean = ContentExtractor.clean_text(text)
        chunks = ContentExtractor.chunk_text(clean)

        for chunk in chunks:
            audio = tts.generate(chunk)
            if audio:
                if not AudioPlayer.play(audio, self.config):
                    Logger.error("Playback failed")
                    return False
        return True

    def run(self) -> int:
        """Main entry point."""
        if self.args.get_clipboard:
            return self.handle_get_clipboard()

        if self.args.list_engines:
            return self.handle_list_engines()

        if self.args.clear_cache:
            return self.handle_clear_cache()

        if not self.args.source:
            return self.run_interactive()

        return self.run_with_source()

    def run_with_source(self) -> int:
        """Run with provided source text/file."""
        text = ContentExtractor.from_source(
            " ".join(self.args.source),
            self.config
        )

        if not text:
            return 1

        clean_text = ContentExtractor.clean_text(text)
        chunks = ContentExtractor.chunk_text(clean_text)

        Logger.log(f"Speaking {len(chunks)} chunks...", self.config)

        tts = TTSEngine(self.config)
        for chunk in chunks:
            audio = tts.generate(chunk)
            if audio and not AudioPlayer.play(audio, self.config):
                Logger.error("Playback failed")
                return 1

        return 0


def main() -> int:
    """Application entry point."""
    return CLI().run()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(0)
