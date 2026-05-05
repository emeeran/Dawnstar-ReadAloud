"""Audio playback helpers."""

import os
import shutil
import subprocess
import tempfile

from .config import TTSConfig
from .constants import TEMP_FILE_SUFFIX
from .logger import Logger


class AudioPlayer:
    """Auto-detecting audio player for MP3/WAV playback."""

    _player_cmd: list[str] | None = None

    PLAYER_CANDIDATES = [
        ("mpg123", ["-q"]),
        ("paplay", []),
        ("cvlc", ["--play-and-exit", "--no-video", "--quiet"]),
        ("ffplay", ["-nodisp", "-autoexit", "-loglevel", "quiet"]),
    ]

    @classmethod
    def get_player(cls) -> list[str] | None:
        if cls._player_cmd:
            return cls._player_cmd

        for bin_name, args in cls.PLAYER_CANDIDATES:
            if shutil.which(bin_name):
                cls._player_cmd = [bin_name] + args
                return cls._player_cmd

        return None

    @classmethod
    def _play_with_temp_file(cls, cmd: list[str], audio_data: bytes) -> bool:
        with tempfile.NamedTemporaryFile(suffix=TEMP_FILE_SUFFIX, delete=False) as temp_file:
            os.chmod(temp_file.name, 0o600)
            temp_file.write(audio_data)
            temp_file.flush()
            temp_path = temp_file.name

        try:
            subprocess.run(cmd + [temp_path], check=True, timeout=300)
            return True
        finally:
            os.unlink(temp_path)

    @classmethod
    def play(cls, audio_data: bytes, config: TTSConfig) -> bool:
        cmd = cls.get_player()
        if not cmd:
            Logger.error("No audio player found")
            return False

        try:
            if cmd[0] == "mpg123":
                process = subprocess.run(
                    cmd + ["-"],
                    input=audio_data,
                    check=True,
                    timeout=300,
                    capture_output=True,
                )
                if process.stderr and config.verbose:
                    print(process.stderr.decode(errors="ignore"))
                return True

            return cls._play_with_temp_file(cmd, audio_data)
        except subprocess.CalledProcessError as error:
            Logger.error(f"Playback error: {error}")
            if error.stderr:
                print(f"  stderr: {error.stderr.decode(errors='ignore')}")
            return False
        except subprocess.TimeoutExpired:
            Logger.error("Playback timeout")
            return False
        except OSError as error:
            Logger.error(f"Playback error: {error}")
            return False
