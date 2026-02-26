"""Command-line interface for the TTS application.

This module provides both a Typer-based modern CLI and backward-compatible
argparse CLI for the TTS application.
"""

import argparse
import os
import subprocess
import sys
from enum import Enum
from typing import List, Optional

from config import TTSAppConfig, generate_sample_config

from .constants import ANSI_CLEAR_LINE, ANSI_GREY_BG, ANSI_RESET, CACHE_DIR
from .config import TTSConfig
from .engine import TTSEngine
from .extractor import ContentExtractor
from .logger import Logger
from .player import AudioPlayer
from .platform import get_clipboard_text
from .runtime import CacheManager, NotificationManager


class SpeedChoice(str, Enum):
    """Speech speed options."""

    SLOW = "slow"
    NORMAL = "normal"
    FAST = "fast"


class CLI:
    """Command-line interface handler.

    This class provides the main CLI implementation using argparse for
    backward compatibility. It handles argument parsing, configuration
    loading, and dispatches to appropriate handlers.

    Attributes:
        app_config: Application configuration loaded from file.
        tts_config: Runtime TTS configuration.
        show_progress: Whether to show progress indicators.
        show_notifications: Whether to show desktop notifications.
    """

    def __init__(self) -> None:
        """Initialize CLI with loaded configuration and parsed arguments."""
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
        """Parse command-line arguments.

        Returns:
            Parsed argument namespace.
        """
        parser = argparse.ArgumentParser(
            prog="tts",
            description="Lightweight Neural TTS - Read text aloud with neural voices",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  tts "Hello world"              Speak text directly
  tts document.txt               Read a file
  tts https://example.com        Read a webpage
  tts -l en-uk -s fast text      Use UK English at fast speed
  tts --clear-cache              Clear audio cache
            """,
        )
        parser.add_argument(
            "source",
            nargs="*",
            help="Text, file path, or URL to read",
        )
        parser.add_argument(
            "-l",
            "--lang",
            default=self.app_config.language,
            choices=["en-us", "en-uk", "ta", "en", "en-gb"],
            help=f"Language code (default: {self.app_config.language})",
        )
        parser.add_argument(
            "-s",
            "--speed",
            default=self.app_config.speed,
            choices=["slow", "normal", "fast"],
            help=f"Speech speed (default: {self.app_config.speed})",
        )
        parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="Enable verbose output",
        )
        parser.add_argument(
            "--no-cache",
            action="store_true",
            help="Disable audio caching",
        )
        parser.add_argument(
            "--clear-cache",
            action="store_true",
            help="Clear the audio cache",
        )
        parser.add_argument(
            "--cache-stats",
            action="store_true",
            help="Show cache statistics",
        )
        parser.add_argument(
            "--list-engines",
            action="store_true",
            help="List available TTS engines",
        )
        parser.add_argument(
            "--get-clipboard",
            action="store_true",
            help="Print clipboard text and exit",
        )
        parser.add_argument(
            "--show-config",
            action="store_true",
            help="Show current configuration",
        )
        parser.add_argument(
            "--generate-config",
            action="store_true",
            help="Generate sample configuration file",
        )
        parser.add_argument(
            "--config-path",
            action="store_true",
            help="Show configuration file path",
        )
        parser.add_argument(
            "--reset-config",
            action="store_true",
            help="Reset configuration to defaults",
        )
        parser.add_argument(
            "--sentence-file",
            metavar="FILE",
            help="Write current sentence to file before speaking (for cursor tracking)",
        )
        return parser.parse_args()

    def handle_get_clipboard(self) -> int:
        """Print clipboard text and exit.

        Returns:
            Exit code (0 on success, 1 if clipboard is empty).
        """
        text = get_clipboard_text()
        if text:
            print(text)
            return 0
        return 1

    def handle_list_engines(self) -> int:
        """List available TTS engines.

        Returns:
            Always returns 0.
        """
        engines = TTSEngine.list_available_engines()
        print("Available TTS engines:")
        for name, available in engines.items():
            status = "ok" if available else "not available"
            print(f"  {name}: {status}")
        return 0

    def handle_clear_cache(self) -> int:
        """Clear the audio cache.

        Returns:
            Always returns 0.
        """
        count = CacheManager.clear()
        print(f"Cleared {count} cached files.")
        return 0

    def handle_cache_stats(self) -> int:
        """Show cache statistics.

        Returns:
            Always returns 0.
        """
        stats = CacheManager.get_cache_stats()
        print("Cache Statistics:")
        print(f"  Files: {stats['files']}")
        print(f"  Size: {stats['size_mb']} MB / {stats['max_size_mb']} MB")
        print(f"  Location: {CACHE_DIR}")
        return 0

    def run_interactive(self) -> int:
        """Run in interactive mode.

        Reads text from stdin line by line until 'quit' is entered.

        Returns:
            Always returns 0.
        """
        print("Interactive mode - type 'quit' to exit")
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
        """Speak the given text using the TTS engine.

        Args:
            text: Text to speak.
            tts: TTS engine instance.

        Returns:
            True if successful, False if playback failed.
        """
        clean = ContentExtractor.clean_text(text)
        chunks = ContentExtractor.chunk_text(clean)

        for chunk in chunks:
            if self.show_progress:
                print(f"{ANSI_GREY_BG}{chunk}{ANSI_RESET}", flush=True)
            audio = tts.generate(chunk)
            if audio and not AudioPlayer.play(audio, self.tts_config):
                Logger.error("Playback failed")
                return False
        return True

    def run(self) -> int:
        """Run the CLI with parsed arguments.

        Returns:
            Exit code (0 on success, non-zero on failure).
        """
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

    def _write_current_sentence(self, sentence: str) -> None:
        """Write current sentence to file if --sentence-file was specified.

        Args:
            sentence: The sentence about to be spoken.
        """
        if hasattr(self.args, 'sentence_file') and self.args.sentence_file:
            try:
                with open(self.args.sentence_file, 'w') as f:
                    f.write(sentence)
            except OSError:
                pass  # Silently ignore file write errors

    def run_with_source(self) -> int:
        """Run with text source (file, URL, or direct text).

        Returns:
            Exit code (0 on success, 1 on failure).
        """
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
            # Write current sentence to file for cursor tracking
            self._write_current_sentence(chunk)

            if self.show_progress:
                # Highlight current sentence with grey background
                print(f"{ANSI_GREY_BG}{chunk}{ANSI_RESET}", flush=True)

            audio = tts.generate(chunk)
            if audio:
                if not AudioPlayer.play(audio, self.tts_config):
                    Logger.error("Playback failed")
                    NotificationManager.notify("TTS", "Playback failed")
                    return 1

        if len(chunks) > 1:
            NotificationManager.notify("TTS", "Finished speaking", timeout=1500)

        return 0
