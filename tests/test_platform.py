"""Unit tests for platform detection module."""

from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.platform import (
    DisplayServer,
    DesktopEnvironment,
    detect_os,
    detect_display_server,
    detect_desktop_environment,
    detect_available_engines,
)


class TestDetectOS:
    """Tests for OS detection."""

    @patch("sys.platform", "darwin")
    def test_detect_macos(self):
        """Test macOS detection."""
        assert detect_os() == "macos"

    @patch("sys.platform", "win32")
    def test_detect_windows(self):
        """Test Windows detection."""
        assert detect_os() == "windows"

    @patch("sys.platform", "linux")
    def test_detect_linux(self):
        """Test Linux detection."""
        assert detect_os() == "linux"


class TestDisplayServer:
    """Tests for display server detection."""

    @patch("sys.platform", "win32")
    def test_windows_display(self):
        """Test Windows display server."""
        assert detect_display_server() == DisplayServer.WINDOWS

    @patch("sys.platform", "darwin")
    def test_macos_display(self):
        """Test macOS display server."""
        assert detect_display_server() == DisplayServer.MACOS

    @patch("sys.platform", "linux")
    @patch.dict("os.environ", {"WAYLAND_DISPLAY": "wayland-0"}, clear=False)
    def test_wayland_detection(self):
        """Test Wayland detection via WAYLAND_DISPLAY."""
        assert detect_display_server() == DisplayServer.WAYLAND

    @patch("sys.platform", "linux")
    @patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}, clear=False)
    def test_wayland_via_session_type(self):
        """Test Wayland detection via XDG_SESSION_TYPE."""
        assert detect_display_server() == DisplayServer.WAYLAND

    @patch("sys.platform", "linux")
    @patch.dict("os.environ", {"DISPLAY": ":0"}, clear=False)
    def test_x11_detection(self):
        """Test X11 detection."""
        assert detect_display_server() == DisplayServer.X11


class TestDesktopEnvironment:
    """Tests for desktop environment detection."""

    @patch("sys.platform", "linux")
    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "GNOME"}, clear=False)
    def test_gnome_detection(self):
        """Test GNOME detection."""
        assert detect_desktop_environment() == DesktopEnvironment.GNOME

    @patch("sys.platform", "linux")
    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "KDE"}, clear=False)
    def test_kde_detection(self):
        """Test KDE detection."""
        assert detect_desktop_environment() == DesktopEnvironment.KDE

    @patch("sys.platform", "linux")
    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "XFCE"}, clear=False)
    def test_xfce_detection(self):
        """Test XFCE detection."""
        assert detect_desktop_environment() == DesktopEnvironment.XFCE

    @patch("sys.platform", "linux")
    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "sway"}, clear=False)
    def test_sway_detection(self):
        """Test Sway detection."""
        assert detect_desktop_environment() == DesktopEnvironment.SWAY

    @patch("sys.platform", "linux")
    @patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "Hyprland"}, clear=False)
    def test_hyprland_detection(self):
        """Test Hyprland detection."""
        assert detect_desktop_environment() == DesktopEnvironment.HYPRLAND

    @patch("sys.platform", "darwin")
    def test_non_linux_returns_unknown(self):
        """Test non-Linux returns unknown."""
        assert detect_desktop_environment() == DesktopEnvironment.UNKNOWN


class TestDetectEngines:
    """Tests for TTS engine detection."""

    @patch("importlib.util.find_spec")
    @patch("shutil.which")
    def test_detect_available_engines(self, mock_which, mock_find_spec):
        """Test engine detection returns correct structure."""
        mock_find_spec.return_value = MagicMock()
        mock_which.return_value = "/usr/bin/espeak"

        engines = detect_available_engines()

        assert isinstance(engines, dict)
        assert "edge" in engines
        assert "gtts" in engines
        assert "espeak" in engines
        assert "piper" in engines

    @patch("importlib.util.find_spec")
    def test_edge_tts_available(self, mock_find_spec):
        """Test Edge TTS availability check."""
        mock_find_spec.return_value = MagicMock()
        engines = detect_available_engines()
        assert engines["edge"] is True

    @patch("importlib.util.find_spec")
    def test_edge_tts_not_available(self, mock_find_spec):
        """Test Edge TTS unavailability."""
        mock_find_spec.side_effect = lambda name: None if name == "edge_tts" else MagicMock()
        engines = detect_available_engines()
        # gtts check might also return None
        assert engines["edge"] is False


class TestEnums:
    """Tests for enum values."""

    def test_display_server_values(self):
        """Test DisplayServer enum values."""
        assert DisplayServer.X11.value == "x11"
        assert DisplayServer.WAYLAND.value == "wayland"
        assert DisplayServer.WINDOWS.value == "windows"
        assert DisplayServer.MACOS.value == "macos"
        assert DisplayServer.UNKNOWN.value == "unknown"

    def test_desktop_environment_values(self):
        """Test DesktopEnvironment enum values."""
        assert DesktopEnvironment.GNOME.value == "gnome"
        assert DesktopEnvironment.KDE.value == "kde"
        assert DesktopEnvironment.XFCE.value == "xfce"
        assert DesktopEnvironment.SWAY.value == "sway"
        assert DesktopEnvironment.HYPRLAND.value == "hyprland"
        assert DesktopEnvironment.UNKNOWN.value == "unknown"
