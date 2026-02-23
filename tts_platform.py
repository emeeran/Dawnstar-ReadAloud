"""
Cross-platform platform detection for TTS application.
Supports: Linux (X11/Wayland), macOS, Windows
"""

import os
import sys
import shutil
import subprocess
from enum import Enum
from typing import Optional


class DisplayServer(Enum):
    X11 = "x11"
    WAYLAND = "wayland"
    WINDOWS = "windows"
    MACOS = "macos"
    UNKNOWN = "unknown"


class DesktopEnvironment(Enum):
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
    if os.getenv('WAYLAND_DISPLAY'):
        return DisplayServer.WAYLAND
    if os.getenv('XDG_SESSION_TYPE', '').lower() == 'wayland':
        return DisplayServer.WAYLAND
    if os.getenv('DISPLAY'):
        return DisplayServer.X11

    return DisplayServer.UNKNOWN


def detect_desktop_environment() -> DesktopEnvironment:
    """Detect Linux desktop environment."""
    if detect_os() != "linux":
        return DesktopEnvironment.UNKNOWN

    xdg_desktop = os.getenv('XDG_CURRENT_DESKTOP', '').upper()

    for de in xdg_desktop.split(':'):
        if de in ['GNOME', 'KDE', 'XFCE', 'SWAY', 'HYPRLAND']:
            return DesktopEnvironment(de.lower())

    # Fallback: Process detection
    try:
        result = subprocess.run(['ps', '-aux'], capture_output=True, text=True, timeout=2)
        output = result.stdout.lower()
        if 'gnome-shell' in output:
            return DesktopEnvironment.GNOME
        if 'plasmashell' in output or 'kde' in output:
            return DesktopEnvironment.KDE
        if 'xfce4-session' in output:
            return DesktopEnvironment.XFCE
        if 'sway' in output:
            return DesktopEnvironment.SWAY
        if 'hyprland' in output:
            return DesktopEnvironment.HYPRLAND
    except:
        pass

    return DesktopEnvironment.UNKNOWN


def get_clipboard_text() -> Optional[str]:
    """Get clipboard text - cross-platform, auto-detects method."""
    os_name = detect_os()

    # Windows
    if os_name == "windows":
        try:
            import win32clipboard
            win32clipboard.OpenClipboard()
            text = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
            return text
        except:
            # Fallback to PowerShell
            try:
                result = subprocess.run(
                    ['powershell', '-Command', 'Get-Clipboard'],
                    capture_output=True, text=True, timeout=2
                )
                return result.stdout.strip() or None
            except:
                return None

    # macOS
    if os_name == "macos":
        try:
            result = subprocess.run(
                ['pbpaste'],
                capture_output=True, text=True, timeout=2
            )
            return result.stdout.strip() or None
        except:
            return None

    # Linux: Try Wayland first, then X11
    display = detect_display_server()

    # Wayland
    if display == DisplayServer.WAYLAND and shutil.which('wl-paste'):
        try:
            result = subprocess.run(
                ['wl-paste', '--no-newline'],
                capture_output=True, text=True, timeout=2
            )
            if result.stdout.strip():
                return result.stdout.strip()
        except:
            pass

    # X11 - Try primary (highlighted), then clipboard (copied)
    if shutil.which('xclip'):
        try:
            # Primary selection (highlighted text)
            result = subprocess.run(
                ['xclip', '-o', '-selection', 'primary'],
                capture_output=True, text=True, timeout=2
            )
            if result.stdout.strip():
                return result.stdout.strip()

            # Clipboard (copied text)
            result = subprocess.run(
                ['xclip', '-o', '-selection', 'clipboard'],
                capture_output=True, text=True, timeout=2
            )
            return result.stdout.strip() or None
        except:
            return None

    return None


def detect_available_engines() -> dict:
    """Detect available TTS engines at runtime."""
    engines = {
        'edge': False,      # edge-tts Python package
        'piper': False,     # Piper binary
        'gtts': False,      # gtts Python package
        'espeak': False,    # espeak binary
    }

    # Check Python packages
    try:
        import edge_tts
        engines['edge'] = True
    except ImportError:
        pass

    try:
        import gtts
        engines['gtts'] = True
    except ImportError:
        pass

    # Check binaries (subprocess)
    if shutil.which('piper'):
        engines['piper'] = True

    if shutil.which('espeak') or shutil.which('espeak-ng'):
        engines['espeak'] = True

    return engines
