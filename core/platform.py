"""
Cross-platform platform detection for TTS application.
Supports: Linux (X11/Wayland), macOS, Windows

This module provides:
- Display server detection (X11, Wayland, Windows, macOS)
- Desktop environment detection (GNOME, KDE, XFCE, etc.)
- Cross-platform clipboard access
- TTS engine availability detection
- Screen reader detection for accessibility
"""

import importlib.util
import os
import shutil
import subprocess
import sys
from enum import Enum


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
    """Detect operating system.

    Returns:
        One of: "macos", "windows", "linux"
    """
    if sys.platform == "darwin":
        return "macos"
    elif sys.platform == "win32":
        return "windows"
    return "linux"


def detect_display_server() -> DisplayServer:
    """Detect active display server.

    Returns:
        DisplayServer enum indicating the current display server.
    """
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
    """Detect Linux desktop environment.

    Returns:
        DesktopEnvironment enum indicating the current desktop environment.
    """
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


def is_screen_reader_active() -> bool:
    """Detect if a screen reader is currently running.

    This function checks for common screen reader processes:
    - Orca (Linux GNOME)
    - NVDA, JAWS (Windows)
    - VoiceOver (macOS)

    Returns:
        True if a screen reader is detected, False otherwise.

    Example:
        >>> if is_screen_reader_active():
        ...     # Use plain text output instead of ANSI codes
        ...     print("Speaking...")
        ... else:
        ...     print("\\033[48;5;238mSpeaking...\\033[0m")
    """
    os_name = detect_os()

    # Screen reader processes by platform
    screen_readers = {
        "linux": ["orca"],
        "windows": ["nvda", "jaws"],
        "macos": ["voiceover"],
    }

    processes_to_check = screen_readers.get(os_name, [])
    if not processes_to_check:
        return False

    try:
        if os_name == "macos":
            # macOS: Check VoiceOver status via AppleScript
            try:
                result = subprocess.run(
                    ["osascript", "-e", "tell application \"System Events\" to get voiceover enabled"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                return "true" in result.stdout.lower()
            except (OSError, subprocess.TimeoutExpired):
                pass
        elif os_name == "windows":
            # Windows: Check for screen reader processes
            try:
                result = subprocess.run(
                    ["tasklist", "/FO", "CSV"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                output = result.stdout.lower()
                return any(sr in output for sr in processes_to_check)
            except (OSError, subprocess.TimeoutExpired):
                pass
        else:
            # Linux: Check for Orca process
            result = subprocess.run(
                ["ps", "-aux"],
                capture_output=True,
                text=True,
                timeout=2
            )
            output = result.stdout.lower()
            return any(sr in output for sr in processes_to_check)

    except (OSError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
        pass

    return False


def supports_ansi_colors() -> bool:
    """Detect if terminal supports ANSI color codes.

    Returns:
        True if ANSI colors are supported, False otherwise.

    Note:
        Returns False if a screen reader is detected to avoid
        confusing output for accessibility users.
    """
    # Don't use ANSI colors if screen reader is active
    if is_screen_reader_active():
        return False

    # Check if stdout is a terminal
    if not sys.stdout.isatty():
        return False

    # Check for NO_COLOR environment variable
    if os.getenv("NO_COLOR"):
        return False

    # Check for forced color mode
    if os.getenv("FORCE_COLOR") or os.getenv("CLICOLOR_FORCE"):
        return True

    # Windows check
    if detect_os() == "windows":  # noqa: SIM103
        # Modern Windows 10 supports ANSI, but be conservative
        return False

    return True


def get_clipboard_text() -> str | None:
    """Get clipboard text - cross-platform, auto-detects method.

    On Linux X11, tries primary selection (highlighted text) first,
    then clipboard selection (Ctrl+C text).

    Returns:
        Clipboard text or None if unavailable.
    """
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

    # X11: Try primary selection (highlighted text) first
    text = _get_clipboard_x11()
    if text:
        return text

    # Fallback to pyperclip for clipboard selection
    try:
        import pyperclip

        text = (pyperclip.paste() or "").strip()
        if text:
            return text
    except (ImportError, Exception):
        pass

    return None


def _get_clipboard_windows() -> str | None:
    """Get clipboard text on Windows.

    Returns:
        Clipboard text or None if unavailable.
    """
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


def _get_clipboard_macos() -> str | None:
    """Get clipboard text on macOS.

    Returns:
        Clipboard text or None if unavailable.
    """
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


def _get_clipboard_wayland() -> str | None:
    """Get clipboard text on Wayland.

    Returns:
        Clipboard text or None if unavailable.
    """
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


def _get_clipboard_x11() -> str | None:
    """Get clipboard text on X11.

    Returns:
        Clipboard text or None if unavailable.
    """
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
    """Detect available TTS engines at runtime.

    Returns:
        Dictionary mapping engine names to availability status.
    """
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


__all__ = [
    "DisplayServer",
    "DesktopEnvironment",
    "detect_os",
    "detect_display_server",
    "detect_desktop_environment",
    "get_clipboard_text",
    "detect_available_engines",
    "is_screen_reader_active",
    "supports_ansi_colors",
]
