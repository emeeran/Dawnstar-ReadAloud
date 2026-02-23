"""
Cross-platform platform detection for TTS application.
Supports: Linux (X11/Wayland), macOS, Windows
"""

import os
import shutil
import subprocess
import sys
import importlib.util
from enum import Enum
from typing import Optional


class DisplayServer(Enum):
    """Supported display servers."""

    X11 = "x11"
    WAYLAND = "wayland"
    WINDOWS = "windows"
    MACOS = "macos"
    UNKNOWN = "unknown"


class DesktopEnvironment(Enum):
    """Supported desktop environments."""

    GNOME = "gnome"
    KDE = "kde"
    XFCE = "xfce"
    SWAY = "sway"
    HYPRLAND = "hyprland"
    UNKNOWN = "unknown"


def detect_os() -> str:
    """Detect operating system."""
    if sys.platform == "darwin":
        return "macos"
    elif sys.platform == "win32":
        return "windows"
    return "linux"


def detect_display_server() -> DisplayServer:
    """Detect active display server."""
    os_name = detect_os()

    if os_name == "windows":
        return DisplayServer.WINDOWS
    if os_name == "macos":
        return DisplayServer.MACOS

    # Linux: Check Wayland first (many run XWayland)
    if os.getenv("WAYLAND_DISPLAY"):
        return DisplayServer.WAYLAND
    if os.getenv("XDG_SESSION_TYPE", "").lower() == "wayland":
        return DisplayServer.WAYLAND
    if os.getenv("DISPLAY"):
        return DisplayServer.X11

    return DisplayServer.UNKNOWN


def detect_desktop_environment() -> DesktopEnvironment:
    """Detect Linux desktop environment."""
    if detect_os() != "linux":
        return DesktopEnvironment.UNKNOWN

    xdg_desktop = os.getenv("XDG_CURRENT_DESKTOP", "").upper()

    for de in xdg_desktop.split(":"):
        if de in ["GNOME", "KDE", "XFCE", "SWAY", "HYPRLAND"]:
            return DesktopEnvironment(de.lower())

    # Fallback: Process detection
    try:
        result = subprocess.run(
            ["ps", "-aux"],
            capture_output=True,
            text=True,
            timeout=2
        )
        output = result.stdout.lower()
        if "gnome-shell" in output:
            return DesktopEnvironment.GNOME
        if "plasmashell" in output or "kde" in output:
            return DesktopEnvironment.KDE
        if "xfce4-session" in output:
            return DesktopEnvironment.XFCE
        if "sway" in output:
            return DesktopEnvironment.SWAY
        if "hyprland" in output:
            return DesktopEnvironment.HYPRLAND
    except (OSError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
        pass

    return DesktopEnvironment.UNKNOWN


def get_clipboard_text() -> Optional[str]:
    """Get clipboard text - cross-platform, auto-detects method."""
    try:
        import pyperclip

        text = (pyperclip.paste() or "").strip()
        if text:
            return text
    except (ImportError, Exception):
        pass

    os_name = detect_os()

    if os_name == "windows":
        return _get_clipboard_windows()

    if os_name == "macos":
        return _get_clipboard_macos()

    # Linux: Try Wayland first, then X11
    display = detect_display_server()

    if display == DisplayServer.WAYLAND:
        text = _get_clipboard_wayland()
        if text:
            return text

    return _get_clipboard_x11()


def _get_clipboard_windows() -> Optional[str]:
    """Get clipboard text on Windows."""
    # Try win32clipboard first
    try:
        import win32clipboard
        win32clipboard.OpenClipboard()
        try:
            text = win32clipboard.GetClipboardData()
            return text
        finally:
            win32clipboard.CloseClipboard()
    except (ImportError, OSError):
        pass

    # Fallback to PowerShell
    try:
        result = subprocess.run(
            ["powershell", "-Command", "Get-Clipboard"],
            capture_output=True,
            text=True,
            timeout=2
        )
        return result.stdout.strip() or None
    except (OSError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
        return None


def _get_clipboard_macos() -> Optional[str]:
    """Get clipboard text on macOS."""
    try:
        result = subprocess.run(
            ["pbpaste"],
            capture_output=True,
            text=True,
            timeout=2
        )
        return result.stdout.strip() or None
    except (OSError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
        return None


def _get_clipboard_wayland() -> Optional[str]:
    """Get clipboard text on Wayland."""
    if not shutil.which("wl-paste"):
        return None

    try:
        result = subprocess.run(
            ["wl-paste", "--no-newline"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.stdout.strip():
            return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
        pass

    return None


def _get_clipboard_x11() -> Optional[str]:
    """Get clipboard text on X11."""
    if not shutil.which("xclip"):
        return None

    try:
        # Primary selection (highlighted text)
        result = subprocess.run(
            ["xclip", "-o", "-selection", "primary"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.stdout.strip():
            return result.stdout.strip()

        # Clipboard (copied text)
        result = subprocess.run(
            ["xclip", "-o", "-selection", "clipboard"],
            capture_output=True,
            text=True,
            timeout=2
        )
        return result.stdout.strip() or None
    except (OSError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
        return None


def detect_available_engines() -> dict:
    """Detect available TTS engines at runtime."""
    engines = {
        "edge": False,
        "piper": False,
        "gtts": False,
        "espeak": False,
    }

    # Check Python packages
    engines["edge"] = importlib.util.find_spec("edge_tts") is not None
    engines["gtts"] = importlib.util.find_spec("gtts") is not None

    # Check binaries
    if shutil.which("piper"):
        engines["piper"] = True

    if shutil.which("espeak") or shutil.which("espeak-ng"):
        engines["espeak"] = True

    return engines
