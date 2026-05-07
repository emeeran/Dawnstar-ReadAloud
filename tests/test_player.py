"""Unit tests for core.player module."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import TTSConfig
from core.player import AudioPlayer


class TestGetPlayer:
    """Tests for AudioPlayer.get_player()."""

    def setup_method(self):
        AudioPlayer._player_cmd = None

    @patch("shutil.which")
    def test_returns_mpg123_when_available(self, mock_which):
        mock_which.side_effect = lambda n: "/usr/bin/mpg123" if n == "mpg123" else None
        assert AudioPlayer.get_player() == ["mpg123", "-q"]

    @patch("shutil.which")
    def test_returns_none_when_nothing_available(self, mock_which):
        mock_which.return_value = None
        assert AudioPlayer.get_player() is None

    @patch("shutil.which")
    def test_caches_result(self, mock_which):
        mock_which.return_value = "/usr/bin/mpg123"
        r1 = AudioPlayer.get_player()
        r2 = AudioPlayer.get_player()
        assert r1 == r2
        assert mock_which.call_count == 1

    @patch("shutil.which")
    def test_falls_back_to_paplay(self, mock_which):
        mock_which.side_effect = lambda n: "/usr/bin/paplay" if n == "paplay" else None
        assert AudioPlayer.get_player() == ["paplay"]

    @patch("shutil.which")
    def test_falls_back_to_cvlc(self, mock_which):
        mock_which.side_effect = lambda n: "/usr/bin/cvlc" if n == "cvlc" else None
        result = AudioPlayer.get_player()
        assert result[0] == "cvlc"
        assert "--play-and-exit" in result


class TestPlay:
    """Tests for AudioPlayer.play()."""

    def setup_method(self):
        AudioPlayer._player_cmd = None

    @patch("shutil.which")
    def test_returns_false_when_no_player(self, mock_which):
        mock_which.return_value = None
        assert AudioPlayer.play(b"data", TTSConfig()) is False

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_mpg123_pipes_via_stdin(self, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/mpg123"
        mock_run.return_value = MagicMock(stderr=b"")
        assert AudioPlayer.play(b"audio", TTSConfig()) is True
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["input"] == b"audio"

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_handles_called_process_error(self, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/mpg123"
        mock_run.side_effect = subprocess.CalledProcessError(1, "mpg123", stderr=b"err")
        assert AudioPlayer.play(b"audio", TTSConfig()) is False

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_handles_timeout(self, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/mpg123"
        mock_run.side_effect = subprocess.TimeoutExpired("mpg123", 300)
        assert AudioPlayer.play(b"audio", TTSConfig()) is False

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_handles_os_error(self, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/mpg123"
        mock_run.side_effect = OSError("fail")
        assert AudioPlayer.play(b"audio", TTSConfig()) is False
