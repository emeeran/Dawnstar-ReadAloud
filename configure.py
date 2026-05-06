#!/usr/bin/env python3
"""
TTS System Configuration Script

Sets up:
- Keyboard shortcuts (multi-DE support)
- Desktop entry
- Wrapper scripts
"""

import os
import shutil
import subprocess
from pathlib import Path

# Configuration
APP_NAME = "Enhanced TTS"
SCRIPT_DIR = Path(__file__).parent
CMD_TTS = Path.home() / ".local/bin/tts"
CMD_STOP = Path.home() / ".local/bin/tts-stop"
CMD_SPEAK = Path.home() / ".local/bin/tts-speak"
CMD_DOC = Path.home() / ".local/bin/tts-doc"
CMD_SELECTION = Path.home() / ".local/bin/tts-selection"


def run_cmd(args: list[str]) -> bool:
    """Run command, return True on success."""
    try:
        subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return False


def check_dependencies():
    """Check system dependencies."""
    print("Checking dependencies...")
    missing = []

    if not shutil.which("xclip") and not shutil.which("wl-paste"):
        missing.append("xclip or wl-paste (clipboard)")

    if not shutil.which("mpg123") and not shutil.which("aplay"):
        missing.append("mpg123 or aplay (audio playback)")

    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        print("   Run: sudo apt install xclip mpg123")
    else:
        print("All dependencies found.")


def install_wrapper_scripts():
    """Install wrapper scripts to ~/.local/bin/."""
    print("Installing wrapper scripts...")

    bin_dir = CMD_TTS.parent
    bin_dir.mkdir(parents=True, exist_ok=True)

    # Main tts command
    tts_content = f"""#!/bin/bash
exec {SCRIPT_DIR.resolve()}/tts "$@"
"""
    CMD_TTS.write_text(tts_content)
    CMD_TTS.chmod(0o755)
    print(f"   Installed: {CMD_TTS}")

    # Stop wrapper
    stop_content = f"""#!/bin/bash
exec {SCRIPT_DIR.resolve()}/stop_speaking.sh "$@"
"""
    CMD_STOP.write_text(stop_content)
    CMD_STOP.chmod(0o755)
    print(f"   Installed: {CMD_STOP}")

    # Speak from cursor wrapper
    speak_content = f"""#!/bin/bash
exec {SCRIPT_DIR.resolve()}/speak_from_cursor.sh "$@"
"""
    CMD_SPEAK.write_text(speak_content)
    CMD_SPEAK.chmod(0o755)
    print(f"   Installed: {CMD_SPEAK}")

    # Read active document wrapper
    doc_content = f"""#!/bin/bash
exec {SCRIPT_DIR.resolve()}/speak_active_doc.sh "$@"
"""
    CMD_DOC.write_text(doc_content)
    CMD_DOC.chmod(0o755)
    print(f"   Installed: {CMD_DOC}")

    # Speak selection wrapper
    selection_content = f"""#!/bin/bash
exec {SCRIPT_DIR.resolve()}/speak_selection.sh "$@"
"""
    CMD_SELECTION.write_text(selection_content)
    CMD_SELECTION.chmod(0o755)
    print(f"   Installed: {CMD_SELECTION}")


def install_systemd_service():
    """Install systemd user service."""
    print("Installing systemd service...")

    service_src = SCRIPT_DIR / "systemd" / "tts-daemon.service"
    service_dir = Path.home() / ".config" / "systemd" / "user"
    service_dir.mkdir(parents=True, exist_ok=True)

    if service_src.exists():
        service_dst = service_dir / "tts-daemon.service"

        # Update paths in service file
        content = service_src.read_text()
        content = content.replace("%h", str(Path.home()))
        content = content.replace("%U", str(os.getuid()))

        service_dst.write_text(content)
        print(f"   Installed: {service_dst}")

        # Reload systemd
        subprocess.run(["systemctl", "--user", "daemon-reload"],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("   Run 'systemctl --user enable tts-daemon' to auto-start")
    else:
        print("   Systemd service file not found (skipping)")


def setup_shortcuts():
    """Set up keyboard shortcuts using DE-specific scripts."""
    print("Setting up keyboard shortcuts...")

    shortcuts_dir = SCRIPT_DIR / "shortcuts"
    install_script = shortcuts_dir / "install.sh"

    if install_script.exists():
        # Run the install script
        result = subprocess.run(
            ["bash", str(install_script)],
            capture_output=False
        )
        if result.returncode != 0:
            print("   Note: Manual setup may be required")
    else:
        print("   Shortcuts installer not found")


def create_desktop_entry():
    """Create desktop entry for application menu."""
    print("Creating desktop entry...")

    desktop_file = Path.home() / ".local/share/applications/tts.desktop"
    desktop_file.parent.mkdir(parents=True, exist_ok=True)

    tts_exec = "tts" if shutil.which("tts") else str(CMD_TTS)

    content = f"""[Desktop Entry]
Type=Application
Name={APP_NAME}
Comment=Speak selected text or files
Exec={tts_exec} %F
Icon=audio-headset
Terminal=true
Categories=Utility;Audio;Accessibility;
Keywords=tts;listen;speech;text-to-speech;
MimeType=text/plain;application/pdf;application/epub+zip;text/markdown;
StartupNotify=false
"""
    desktop_file.write_text(content)
    desktop_file.chmod(0o755)
    print(f"   Installed: {desktop_file}")


def main():
    print(f"--- {APP_NAME} Setup ---")
    print()

    check_dependencies()
    print()

    install_wrapper_scripts()
    print()

    install_systemd_service()
    print()

    create_desktop_entry()
    print()

    setup_shortcuts()
    print()

    print("Setup Complete!")
    print()
    print("Usage:")
    print("  tts 'Hello world'         - Speak text")
    print("  tts document.txt          - Read file")
    print("  ttsc --daemon --fork      - Start daemon in background")
    print("  ttsc speak 'text'         - Speak via daemon")
    print("  ttsc stop                 - Stop speaking")
    print()
    print("Keyboard shortcuts:")
    print("  Shift+Alt+S - Read active document")
    print("  Shift+Alt+C - Speak selection")
    print("  Shift+Alt+Q - Stop speaking")
    print()
    print("You may need to log out and back in for shortcuts to take effect.")


if __name__ == "__main__":
    main()
