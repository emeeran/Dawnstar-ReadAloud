#!/usr/bin/env python3
"""Enhanced Text-to-Speech Application"""
import sys, os, re, subprocess, hashlib, argparse, tempfile, shutil
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass
from abc import ABC, abstractmethod

import tts_platform

CACHE_DIR = Path.home() / ".cache" / "tts_app"
CHUNK_SIZE = 500
DEFAULT_LANG = "en-us"
LANG_CONFIG = {
    "en-us": {"name": "English (US)", "voice": "en-US-GuyNeural", "fallback_tld": "us"},
    "en-uk": {"name": "English (UK)", "voice": "en-GB-RyanNeural", "fallback_tld": "co.uk"},
    "ta": {"name": "Tamil", "voice": "ta-IN-ValluvarNeural", "fallback_tld": None}
}
SPEED_MAP = {"slow": "-25%", "normal": "+0%", "fast": "+25%"}

@dataclass
class TTSConfig:
    lang: str = DEFAULT_LANG
    cache_enabled: bool = True
    verbose: bool = False
    speed: str = "normal"
    engine: Optional[str] = None
    def __post_init__(self):
        if self.lang not in LANG_CONFIG:
            self.lang = {"en": "en-us", "en-gb": "en-uk"}.get(self.lang, DEFAULT_LANG)
        if self.cache_enabled:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)

class Logger:
    @staticmethod
    def log(msg: str, config: TTSConfig):
        if config.verbose:
            print(f"✓ {msg}")

class ContentExtractor:
    @staticmethod
    def clean_text(text: str) -> str:
        text = re.sub(r"http[s]?://\\S+", "", text)
        text = re.sub(r"\\S+@\\S+", "", text)
        return text.strip()
    @staticmethod
    def chunk_text(text: str, size: int = CHUNK_SIZE) -> List[str]:
        if len(text) <= size:
            return [text]
        chunks, pos = [], 0
        while pos < len(text):
            end = min(pos + size, len(text))
            chunk = text[pos:end]
            for char in [". ", "! ", "? ", "; ", ": ", ", ", " "]:
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
        if source == "-":
            return sys.stdin.read()
        source = source.strip().strip("'").strip('"')
        if os.path.exists(source):
            try:
                return Path(source).read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                Logger.log(f"Read error: {e}", config)
                return None
        return source

class AudioPlayer:
    _player_cmd: Optional[List[str]] = None
    @classmethod
    def get_player(cls) -> Optional[List[str]]:
        if cls._player_cmd:
            return cls._player_cmd
        for bin_name, args in [("mpg123", ["-q"]), ("paplay", []), ("cvlc", ["--play-and-exit", "--no-video", "--quiet"]), ("ffplay", ["-nodisp", "-autoexit", "-loglevel", "quiet"])]:
            if shutil.which(bin_name):
                cls._player_cmd = [bin_name] + args
                return cls._player_cmd
        return None
    @classmethod
    def play(cls, audio_data: bytes, config: TTSConfig) -> bool:
        cmd = cls.get_player()
        if not cmd:
            print("No audio player found")
            return False
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tf:
            tf.write(audio_data)
            tf.flush()
            try:
                subprocess.run(cmd + [tf.name], check=True, timeout=300)
                return True
            except subprocess.CalledProcessError as e:
                print(f"Playback error: {e}")
                if e.stderr:
                    print(f"stderr: {e.stderr.decode()}")
                return False
            except Exception as e:
                print(f"Playback error: {e}")
                return False
            finally:
                os.unlink(tf.name)

class TTSBackend(ABC):
    def __init__(self, config: TTSConfig):
        self.config = config
        self.voice = LANG_CONFIG[config.lang]["voice"]
        self.rate = SPEED_MAP[config.speed]
    @abstractmethod
    def is_available(self) -> bool: pass
    @abstractmethod
    def generate_audio(self, text: str) -> bytes: pass
    def get_name(self) -> str: return self.__class__.__name__

class EdgeTTSBackend(TTSBackend):
    @staticmethod
    def _find_edge_binary() -> Optional[str]:
        script_dir = Path(__file__).parent
        for p in [script_dir / "venv" / "bin" / "edge-tts", script_dir / ".venv" / "bin" / "edge-tts", Path(sys.executable).parent / "edge-tts"]:
            if p.exists():
                return str(p)
        return shutil.which("edge-tts")
    def is_available(self) -> bool:
        return self._find_edge_binary() is not None
    def generate_audio(self, text: str) -> bytes:
        edge_bin = self._find_edge_binary() or "edge-tts"
        with tempfile.NamedTemporaryFile(suffix=".mp3") as tf:
            subprocess.run([edge_bin, "--voice", self.voice, "--rate", self.rate, "--text", text, "--write-media", tf.name], check=True, capture_output=True)
            return Path(tf.name).read_bytes()

class GTTSBackend(TTSBackend):
    def is_available(self) -> bool:
        try:
            import gtts
            return True
        except ImportError:
            return False
    def generate_audio(self, text: str) -> bytes:
        from gtts import gTTS
        tld = LANG_CONFIG[self.config.lang]["fallback_tld"]
        lang = "en" if "en" in self.config.lang else "ta"
        tts = gTTS(text=text, lang=lang, tld=tld or "com", slow=self.config.speed == "slow")
        with tempfile.NamedTemporaryFile(suffix=".mp3") as tf:
            tts.save(tf.name)
            return Path(tf.name).read_bytes()

class EspeakBackend(TTSBackend):
    def is_available(self) -> bool:
        return shutil.which("espeak-ng") is not None or shutil.which("espeak") is not None
    def generate_audio(self, text: str) -> bytes:
        espeak_bin = "espeak-ng" if shutil.which("espeak-ng") else "espeak"
        speed = {"slow": "120", "normal": "160", "fast": "200"}[self.config.speed]
        voice = {"en-us": "en-us", "en-uk": "en-uk", "ta": "ta-in"}.get(self.config.lang, "en-us")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
            subprocess.run([espeak_bin, "-v", voice, "-s", speed, "-w", tf.name], input=text.encode(), capture_output=True, check=True)
            data = Path(tf.name).read_bytes()
            os.unlink(tf.name)
            return data

class TTSEngine:
    def __init__(self, config: TTSConfig):
        self.config = config
        self._backends: Optional[List[TTSBackend]] = None
    @property
    def backends(self) -> List[TTSBackend]:
        if self._backends is None:
            self._backends = []
            for bc in [EdgeTTSBackend, GTTSBackend, EspeakBackend]:
                b = bc(self.config)
                if b.is_available():
                    self._backends.append(b)
        return self._backends
    def generate(self, text: str) -> Optional[bytes]:
        ckey = hashlib.md5(f"{text}_{self.config.lang}_{self.config.speed}".encode()).hexdigest()
        cfile = CACHE_DIR / f"{ckey}.mp3"
        if self.config.cache_enabled and cfile.exists():
            Logger.log("Cache hit", self.config)
            return cfile.read_bytes()
        for backend in self.backends:
            try:
                data = backend.generate_audio(text)
                if self.config.cache_enabled:
                    cfile.write_bytes(data)
                Logger.log(f"Generated with {backend.get_name()}", self.config)
                return data
            except Exception:
                pass
        return None
    @staticmethod
    def list_available_engines() -> Dict[str, bool]:
        script_dir = Path(__file__).parent
        return {
            "edge": (script_dir / "venv" / "bin" / "edge-tts").exists() or shutil.which("edge-tts") is not None,
            "gtts": True,
            "espeak": shutil.which("espeak-ng") is not None or shutil.which("espeak") is not None,
        }

def main():
    parser = argparse.ArgumentParser(description="Lightweight Neural TTS")
    parser.add_argument("source", nargs="*")
    parser.add_argument("-l", "--lang", default=DEFAULT_LANG)
    parser.add_argument("-s", "--speed", default="normal", choices=["slow", "normal", "fast"])
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--clear-cache", action="store_true")
    parser.add_argument("--list-engines", action="store_true")
    parser.add_argument("--get-clipboard", action="store_true", help="Print clipboard text and exit")
    args = parser.parse_args()
    if args.get_clipboard:
        text = tts_platform.get_clipboard_text()
        if text:
            print(text)
            return 0
        return 1
    if args.list_engines:
        engines = TTSEngine.list_available_engines()
        print("Available TTS engines:")
        for name, avail in engines.items():
            print(f"  {'✓' if avail else '✗'} {name}")
        return 0
    if args.clear_cache:
        if CACHE_DIR.exists():
            shutil.rmtree(CACHE_DIR)
        print("Done.")
        return 0
    config = TTSConfig(args.lang, not args.no_cache, args.verbose, args.speed)
    if not args.source:
        print("Interactive mode - 'quit' to exit")
        while True:
            text = input("> ")
            if text.lower() == "quit":
                break
            if text:
                clean = ContentExtractor.clean_text(text)
                chunks = ContentExtractor.chunk_text(clean)
                tts = TTSEngine(config)
                for chunk in chunks:
                    audio = tts.generate(chunk)
                    if audio:
                        AudioPlayer.play(audio, config)
        return 0
    text = ContentExtractor.from_source(" ".join(args.source), config)
    if not text:
        return 1
    clean_text = ContentExtractor.clean_text(text)
    chunks = ContentExtractor.chunk_text(clean_text)
    Logger.log(f"Speaking {len(chunks)} chunks...", config)
    tts = TTSEngine(config)
    for chunk in chunks:
        audio = tts.generate(chunk)
        if audio and not AudioPlayer.play(audio, config):
            print("Playback failed")

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\\nStopped.")
        sys.exit(0)
