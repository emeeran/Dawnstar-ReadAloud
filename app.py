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
from config import TTSAppConfig, generate_sample_config, CONFIG_DIR

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
    """Find edge-tts binary in venv or system PATH (cached)."""
    if find_edge_tts_binary._cached is not None:
        return find_edge_tts_binary._cached

    script_dir = Path(__file__).parent
    search_paths = [
        script_dir / "venv" / "bin" / "edge-tts",
        script_dir / ".venv" / "bin" / "edge-tts",
        Path(sys.executable).parent / "edge-tts",
    ]
    for path in search_paths:
        if path.exists():
            find_edge_tts_binary._cached = str(path)
            return find_edge_tts_binary._cached

    result = shutil.which("edge-tts")
    find_edge_tts_binary._cached = result
    return result


find_edge_tts_binary._cached = None  # type: ignore[attr-defined]


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


# Pre-compiled regex patterns for text cleaning
_RE_URL = re.compile(r"http[s]?://\S+")
_RE_EMAIL = re.compile(r"\S+@\S+")


class ContentExtractor:
    """Extract and process text content from various sources."""

    @staticmethod
    def clean_text(text: str) -> str:
        """Remove URLs, emails, and normalize whitespace."""
        text = _RE_URL.sub("", text)
        text = _RE_EMAIL.sub("", text)
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
            # Validate path - resolve and check it's safe
            try:
                resolved_path = Path(source).resolve()
            except (OSError, ValueError) as e:
                Logger.log(f"Invalid path: {e}", config)
                return None

            # Security check: prevent reading sensitive system files
            # Allow only: user home, /tmp, /var/tmp, and relative paths
            home = Path.home()
            allowed_prefixes = [home, Path("/tmp"), Path("/var/tmp")]

            is_allowed = any(
                str(resolved_path).startswith(str(p)) for p in allowed_prefixes
            )

            # Also allow relative paths in current directory
            if not is_allowed and not source.startswith("/"):
                is_allowed = True

            if not is_allowed:
                Logger.log(f"Access denied: path outside allowed directories", config)
                return None

            # Check file type
            source_lower = source.lower()

            if source_lower.endswith(".epub"):
                return cls._extract_epub(str(resolved_path), config)

            if source_lower.endswith(".pdf"):
                return cls._extract_pdf(str(resolved_path), config)

            # Default: read as plain text
            try:
                return resolved_path.read_text(encoding="utf-8", errors="ignore")
            except OSError as e:
                Logger.log(f"Read error: {e}", config)
                return None

        return source

    # Patterns for front matter to skip (matched against filename and title)
    # Use word boundaries to avoid false positives
    FRONT_MATTER_PATTERNS = [
        r'(?:^|[/\s])toc(?:[/\s\.]|$)',  # TOC as standalone word
        r'table\s+of\s+contents?',
        r'\bpreface\b', r'\bforeword\b', r'\bprologue\b',
        r'\bcopyright\b', r'\bdedication\b',
        r'about\s+the\s+author', r'about\s+the\s+publisher',
        r'\backnowledge?ments?\b', r'\bcredits\b',
        r'\bcover(?:\s+page)?\b', r'\btitle\s+page\b',
        r'\bepigraph\b', r'\bfrontispiece\b',
        r'series\s+page', r'also\s+by\s+\w', r'praise\s+for',
        r'advanced\s+praise', r'\bendorsements?\b',
        r'\bappendix\b', r'\bbibliography\b',
        r'\bindex\b', r'\bglossary\b', r'\breferences?\b',
    ]

    @staticmethod
    def _is_front_matter(filename: str, title: str = "") -> bool:
        """Check if a document is front/back matter to skip."""
        import re

        check = f"{filename} {title}".lower()

        for pattern in ContentExtractor.FRONT_MATTER_PATTERNS:
            if re.search(pattern, check, re.IGNORECASE):
                return True

        return False

    @staticmethod
    def _extract_epub(path: str, config: TTSConfig) -> Optional[str]:
        """Extract text content from EPUB file, skipping front/back matter."""
        try:
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup

            book = epub.read_epub(path)

            # Collect all document items with their metadata
            documents = []
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    # Get filename/id
                    filename = item.get_name() or item.get_id() or ""
                    documents.append((filename, item))

            # Separate front matter from main content
            main_content = []
            found_chapter = False
            skip_count = 0

            for filename, item in documents:
                # Parse content
                soup = BeautifulSoup(item.get_content(), "html.parser")

                # Get title from first heading
                title = ""
                for tag in ['h1', 'h2', 'title']:
                    heading = soup.find(tag)
                    if heading:
                        title = heading.get_text(strip=True)
                        break

                # Check if this is front matter
                is_front = ContentExtractor._is_front_matter(filename, title)

                # Also skip very short documents at the start (likely copyright, etc.)
                text = soup.get_text(separator=" ")
                clean_text = " ".join(text.split())
                word_count = len(clean_text.split())

                if not found_chapter:
                    if is_front or (word_count < 100 and skip_count < 5):
                        skip_count += 1
                        if config.verbose:
                            print(f"  Skipping: {filename} ({word_count} words)")
                        continue
                    else:
                        found_chapter = True

                # Remove script and style elements
                for script in soup(["script", "style", "nav"]):
                    script.decompose()

                text = soup.get_text(separator=" ")
                text = " ".join(text.split())

                if text.strip() and word_count >= 20:
                    main_content.append(text.strip())

            return " ".join(main_content)

        except ImportError:
            Logger.log("ebooklib or beautifulsoup4 required for EPUB support", config)
            print("Install with: pip install ebooklib beautifulsoup4")
            return None
        except (OSError, ValueError, KeyError, AttributeError) as e:
            Logger.log(f"EPUB read error: {e}", config)
            return None

    @staticmethod
    def _extract_pdf(path: str, config: TTSConfig) -> Optional[str]:
        """Extract text from PDF, skipping front matter (first few pages)."""
        try:
            import subprocess

            # Check for pdftotext
            if not shutil.which("pdftotext"):
                Logger.log("pdftotext required for PDF support", config)
                print("Install with: sudo apt install poppler-utils")
                return None

            # Get page count
            result = subprocess.run(
                ["pdfinfo", path],
                capture_output=True, text=True, timeout=10
            )

            page_count = 0
            for line in result.stdout.split('\n'):
                if line.startswith('Pages:'):
                    page_count = int(line.split(':')[1].strip())
                    break

            if page_count == 0:
                # Fallback: try reading whole file
                result = subprocess.run(
                    ["pdftotext", "-layout", path, "-"],
                    capture_output=True, text=True, timeout=60
                )
                return result.stdout.strip()

            # Skip first 2-3 pages for typical books (TOC, copyright)
            # For short documents (< 10 pages), skip only first page
            skip_pages = min(3, max(1, page_count // 10))

            # Extract text from remaining pages
            # pdftotext doesn't support page ranges directly, so we extract all
            result = subprocess.run(
                ["pdftotext", "-layout", path, "-"],
                capture_output=True, text=True, timeout=120
            )

            text = result.stdout.strip()

            # Try to find where actual content starts by looking for chapter markers
            lines = text.split('\n')
            content_start = 0
            found_chapter = False

            # Look for common chapter indicators
            chapter_patterns = [
                r'^chapter\s+\d+',
                r'^chapter\s+one\b',
                r'^part\s+one\b',
                r'^1\s*$',
                r'^\d+\.\s+\w',  # Numbered sections
            ]

            for i, line in enumerate(lines[:100]):  # Check first 100 lines
                line_stripped = line.strip().lower()
                for pattern in chapter_patterns:
                    if re.match(pattern, line_stripped):
                        content_start = i
                        found_chapter = True
                        break
                if found_chapter:
                    break

            if content_start > 0:
                text = '\n'.join(lines[content_start:])

            return text

        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            Logger.log(f"PDF read error: {e}", config)
            return None


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

    # Cache availability check result
    _available: Optional[bool] = None

    def is_available(self) -> bool:
        """Check if gtts is available (cached result)."""
        if GTTSBackend._available is not None:
            return GTTSBackend._available

        try:
            import importlib.util
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
            slow=self.config.speed == "slow"
        )

        with tempfile.NamedTemporaryFile(suffix=TEMP_FILE_SUFFIX) as tf:
            tts.save(tf.name)
            return Path(tf.name).read_bytes()


class EspeakBackend(TTSBackend):
    """eSpeak-ng backend for basic TTS."""

    _binary_cache: Optional[str] = None

    @classmethod
    def _find_binary(cls) -> Optional[str]:
        """Find espeak binary (cached)."""
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


class NotificationManager:
    """Desktop notification support."""

    _enabled: bool = True
    _available: Optional[bool] = None

    @classmethod
    def is_available(cls) -> bool:
        """Check if notify-send is available."""
        if cls._available is None:
            cls._available = shutil.which("notify-send") is not None
        return cls._available

    @classmethod
    def notify(cls, title: str, message: str, timeout: int = 2000) -> bool:
        """Send a desktop notification."""
        if not cls._enabled or not cls.is_available():
            return False

        try:
            subprocess.run(
                ["notify-send", "-t", str(timeout), title, message],
                capture_output=True,
                timeout=5
            )
            return True
        except (OSError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return False

    @classmethod
    def set_enabled(cls, enabled: bool) -> None:
        """Enable or disable notifications."""
        cls._enabled = enabled


class CacheManager:
    """LRU cache manager with size limits."""

    _initialized: bool = False
    _max_size_bytes: int = 500 * 1024 * 1024  # 500 MB default

    @classmethod
    def initialize(cls, max_size_mb: int = 500) -> None:
        """Initialize cache with size limit."""
        if cls._initialized:
            return
        cls._max_size_bytes = max_size_mb * 1024 * 1024
        cls._initialized = True
        cls._enforce_limit()

    @classmethod
    def get_cache_stats(cls) -> Dict[str, any]:
        """Get cache statistics."""
        if not CACHE_DIR.exists():
            return {"files": 0, "size_bytes": 0, "size_mb": 0.0}

        total_size = 0
        file_count = 0
        for f in CACHE_DIR.glob("*.mp3"):
            try:
                total_size += f.stat().st_size
                file_count += 1
            except OSError:
                pass

        return {
            "files": file_count,
            "size_bytes": total_size,
            "size_mb": round(total_size / (1024 * 1024), 2),
            "max_size_mb": cls._max_size_bytes // (1024 * 1024),
        }

    @classmethod
    def _enforce_limit(cls) -> None:
        """Remove oldest files if cache exceeds size limit."""
        if not CACHE_DIR.exists():
            return

        # Get all cache files sorted by modification time (oldest first)
        files = []
        total_size = 0
        for f in CACHE_DIR.glob("*.mp3"):
            try:
                mtime = f.stat().st_mtime
                size = f.stat().st_size
                files.append((mtime, f, size))
                total_size += size
            except OSError:
                pass

        # Remove oldest files until under limit
        files.sort()  # Oldest first
        for mtime, f, size in files:
            if total_size <= cls._max_size_bytes:
                break
            try:
                f.unlink()
                total_size -= size
            except OSError:
                pass

    @classmethod
    def clear(cls) -> int:
        """Clear all cache files, return count of deleted files."""
        if not CACHE_DIR.exists():
            return 0

        count = 0
        for f in CACHE_DIR.glob("*.mp3"):
            try:
                f.unlink()
                count += 1
            except OSError:
                pass
        return count


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

    # Limits for safety
    MAX_TEXT_LENGTH = 50000  # ~50KB of text max
    GENERATION_TIMEOUT = 60  # seconds

    def generate(self, text: str) -> Optional[bytes]:
        """Generate audio for text, using cache if available."""
        # Input validation
        if not text or not text.strip():
            return None

        # Truncate excessively long text to prevent resource exhaustion
        if len(text) > self.MAX_TEXT_LENGTH:
            text = text[:self.MAX_TEXT_LENGTH]
            Logger.log(f"Text truncated to {self.MAX_TEXT_LENGTH} chars", self.config)

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
            except (subprocess.CalledProcessError, OSError, RuntimeError,
                    subprocess.TimeoutExpired) as e:
                if self.config.verbose:
                    print(f"  Backend {backend.get_name()} failed: {e}")
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
        # Load config file first
        self.app_config = TTSAppConfig.load()
        self.args = self._parse_args()

        # CLI args override config file
        self.tts_config = TTSConfig(
            lang=self.args.lang,
            cache_enabled=not self.args.no_cache,
            verbose=self.args.verbose or self.app_config.verbose,
            speed=self.args.speed,
        )

        # Store app-level config for notifications, progress, etc.
        self.show_progress = self.app_config.progress
        self.show_notifications = self.app_config.notifications

        # Initialize cache with size limit
        CacheManager.initialize(self.app_config.cache_max_size_mb)

        # Set notification preference
        NotificationManager.set_enabled(self.show_notifications)

    def _parse_args(self) -> argparse.Namespace:
        """Parse command-line arguments with config file defaults."""
        parser = argparse.ArgumentParser(description="Lightweight Neural TTS")
        parser.add_argument("source", nargs="*")
        parser.add_argument(
            "-l", "--lang",
            default=self.app_config.language,
            help=f"Language (default: {self.app_config.language})"
        )
        parser.add_argument(
            "-s", "--speed",
            default=self.app_config.speed,
            choices=["slow", "normal", "fast"],
            help=f"Speech speed (default: {self.app_config.speed})"
        )
        parser.add_argument("-v", "--verbose", action="store_true")
        parser.add_argument("--no-cache", action="store_true")
        parser.add_argument("--clear-cache", action="store_true")
        parser.add_argument("--cache-stats", action="store_true",
                           help="Show cache statistics")
        parser.add_argument("--list-engines", action="store_true")
        parser.add_argument(
            "--get-clipboard",
            action="store_true",
            help="Print clipboard text and exit"
        )
        # Config management
        parser.add_argument(
            "--show-config",
            action="store_true",
            help="Show current configuration"
        )
        parser.add_argument(
            "--generate-config",
            action="store_true",
            help="Generate sample config file"
        )
        parser.add_argument(
            "--config-path",
            action="store_true",
            help="Show config file path"
        )
        parser.add_argument(
            "--reset-config",
            action="store_true",
            help="Reset configuration to defaults"
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
        count = CacheManager.clear()
        print(f"Cleared {count} cached files.")
        return 0

    def handle_cache_stats(self) -> int:
        """Handle --cache-stats flag."""
        stats = CacheManager.get_cache_stats()
        print("Cache Statistics:")
        print(f"  Files: {stats['files']}")
        print(f"  Size: {stats['size_mb']} MB / {stats['max_size_mb']} MB")
        print(f"  Location: {CACHE_DIR}")
        return 0

    def run_interactive(self) -> int:
        """Run interactive mode."""
        print("Interactive mode - 'quit' to exit")
        tts = TTSEngine(self.tts_config)

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
                if not AudioPlayer.play(audio, self.tts_config):
                    Logger.error("Playback failed")
                    return False
        return True

    def run(self) -> int:
        """Main entry point."""
        # Config management options
        if self.args.config_path:
            print(TTSAppConfig.get_config_path())
            return 0

        if self.args.generate_config:
            print(generate_sample_config())
            return 0

        if self.args.show_config:
            self._show_config()
            return 0

        if self.args.reset_config:
            if TTSAppConfig.reset():
                print("Configuration reset to defaults.")
            else:
                print("Failed to reset configuration.")
            return 0

        if self.args.get_clipboard:
            return self.handle_get_clipboard()

        if self.args.list_engines:
            return self.handle_list_engines()

        if self.args.clear_cache:
            return self.handle_clear_cache()

        if self.args.cache_stats:
            return self.handle_cache_stats()

        if not self.args.source:
            return self.run_interactive()

        return self.run_with_source()

    def _show_config(self) -> None:
        """Display current configuration."""
        print(f"Configuration file: {TTSAppConfig.get_config_path()}")
        print(f"Source: {self.app_config._source}")
        print()
        for key, value in self.app_config.to_dict().items():
            print(f"  {key}: {value}")

    def run_with_source(self) -> int:
        """Run with provided source text/file."""
        text = ContentExtractor.from_source(
            " ".join(self.args.source),
            self.tts_config
        )

        if not text:
            return 1

        clean_text = ContentExtractor.clean_text(text)
        chunks = ContentExtractor.chunk_text(clean_text)

        Logger.log(f"Speaking {len(chunks)} chunks...", self.tts_config)

        # Show notification for longer texts
        if len(chunks) > 1:
            NotificationManager.notify(
                "TTS",
                f"Speaking {len(chunks)} segments...",
                timeout=2000
            )

        tts = TTSEngine(self.tts_config)
        for i, chunk in enumerate(chunks, 1):
            audio = tts.generate(chunk)
            if audio:
                if self.show_progress and len(chunks) > 1:
                    print(f"[{i}/{len(chunks)}]", end=" ", flush=True)
                if not AudioPlayer.play(audio, self.tts_config):
                    Logger.error("Playback failed")
                    NotificationManager.notify("TTS", "Playback failed")
                    return 1

        if self.show_progress and len(chunks) > 1:
            print()  # New line after progress

        # Completion notification for longer texts
        if len(chunks) > 1:
            NotificationManager.notify("TTS", "Finished speaking", timeout=1500)

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
