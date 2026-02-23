"""Command-line interface for the TTS application."""

import argparse

import tts_platform
from config import TTSAppConfig, generate_sample_config

from .constants import CACHE_DIR
from .config import TTSConfig
from .engine import TTSEngine
from .extractor import ContentExtractor
from .logger import Logger
from .player import AudioPlayer
from .runtime import CacheManager, NotificationManager


class CLI:
    """Command-line interface handler."""

    def __init__(self) -> None:
        self.app_config = TTSAppConfig.load()
        self.args = self._parse_args()

        self.tts_config = TTSConfig(
            lang=self.args.lang,
            cache_enabled=not self.args.no_cache,
            verbose=self.args.verbose or self.app_config.verbose,
            speed=self.args.speed,
        )

        self.show_progress = self.app_config.progress
        self.show_notifications = self.app_config.notifications

        CacheManager.initialize(self.app_config.cache_max_size_mb)
        NotificationManager.set_enabled(self.show_notifications)

    def _parse_args(self) -> argparse.Namespace:
        parser = argparse.ArgumentParser(description="Lightweight Neural TTS")
        parser.add_argument("source", nargs="*")
        parser.add_argument(
            "-l",
            "--lang",
            default=self.app_config.language,
            help=f"Language (default: {self.app_config.language})",
        )
        parser.add_argument(
            "-s",
            "--speed",
            default=self.app_config.speed,
            choices=["slow", "normal", "fast"],
            help=f"Speech speed (default: {self.app_config.speed})",
        )
        parser.add_argument("-v", "--verbose", action="store_true")
        parser.add_argument("--no-cache", action="store_true")
        parser.add_argument("--clear-cache", action="store_true")
        parser.add_argument("--cache-stats", action="store_true", help="Show cache statistics")
        parser.add_argument("--list-engines", action="store_true")
        parser.add_argument("--get-clipboard", action="store_true", help="Print clipboard text and exit")
        parser.add_argument("--show-config", action="store_true", help="Show current configuration")
        parser.add_argument("--generate-config", action="store_true", help="Generate sample config file")
        parser.add_argument("--config-path", action="store_true", help="Show config file path")
        parser.add_argument("--reset-config", action="store_true", help="Reset configuration to defaults")
        return parser.parse_args()

    def handle_get_clipboard(self) -> int:
        text = tts_platform.get_clipboard_text()
        if text:
            print(text)
            return 0
        return 1

    def handle_list_engines(self) -> int:
        engines = TTSEngine.list_available_engines()
        print("Available TTS engines:")
        for name, available in engines.items():
            status = "✓" if available else "✗"
            print(f"  {status} {name}")
        return 0

    def handle_clear_cache(self) -> int:
        count = CacheManager.clear()
        print(f"Cleared {count} cached files.")
        return 0

    def handle_cache_stats(self) -> int:
        stats = CacheManager.get_cache_stats()
        print("Cache Statistics:")
        print(f"  Files: {stats['files']}")
        print(f"  Size: {stats['size_mb']} MB / {stats['max_size_mb']} MB")
        print(f"  Location: {CACHE_DIR}")
        return 0

    def run_interactive(self) -> int:
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
        clean = ContentExtractor.clean_text(text)
        chunks = ContentExtractor.chunk_text(clean)

        for chunk in chunks:
            audio = tts.generate(chunk)
            if audio and not AudioPlayer.play(audio, self.tts_config):
                Logger.error("Playback failed")
                return False
        return True

    def run(self) -> int:
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
        print(f"Configuration file: {TTSAppConfig.get_config_path()}")
        print(f"Source: {self.app_config._source}")
        print()
        for key, value in self.app_config.to_dict().items():
            print(f"  {key}: {value}")

    def run_with_source(self) -> int:
        text = ContentExtractor.from_source(" ".join(self.args.source), self.tts_config)
        if not text:
            return 1

        clean_text = ContentExtractor.clean_text(text)
        chunks = ContentExtractor.chunk_text(clean_text)

        Logger.log(f"Speaking {len(chunks)} chunks...", self.tts_config)

        if len(chunks) > 1:
            NotificationManager.notify("TTS", f"Speaking {len(chunks)} segments...", timeout=2000)

        tts = TTSEngine(self.tts_config)
        for index, chunk in enumerate(chunks, 1):
            audio = tts.generate(chunk)
            if audio:
                if self.show_progress and len(chunks) > 1:
                    print(f"[{index}/{len(chunks)}]", end=" ", flush=True)
                if not AudioPlayer.play(audio, self.tts_config):
                    Logger.error("Playback failed")
                    NotificationManager.notify("TTS", "Playback failed")
                    return 1

        if self.show_progress and len(chunks) > 1:
            print()

        if len(chunks) > 1:
            NotificationManager.notify("TTS", "Finished speaking", timeout=1500)

        return 0
