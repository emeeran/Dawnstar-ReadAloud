#!/usr/bin/env python3
"""Detect the active window's document source (file path or URL).

Outputs a file path or URL if detected, exits with code 1 otherwise.
Used by speak_from_cursor.sh to read the focused document via `tts <source>`.
"""

import os
import re
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def get_active_window_id() -> str:
    return _run(["xdotool", "getactivewindow"])


def get_window_class(wid: str) -> str:
    raw = _run(["xprop", "-id", wid, "WM_CLASS"])
    matches = re.findall(r'"([^"]+)"', raw)
    return " ".join(m.lower() for m in matches)


def get_window_title(wid: str) -> str:
    return _run(["xdotool", "getwindowname", wid])


def get_browser_url(wid: str) -> str | None:
    """Extract URL from browser address bar via xdotool."""
    old = _run(["xclip", "-o", "-selection", "clipboard"])

    try:
        _run(["xdotool", "key", "--window", wid, "ctrl+l"])
        _run(["sleep", "0.2"])
        _run(["xdotool", "key", "--window", wid, "ctrl+c"])
        _run(["sleep", "0.2"])
        url = _run(["xclip", "-o", "-selection", "clipboard"])

        if url.startswith(("http://", "https://")):
            return url
    except (OSError, subprocess.TimeoutExpired):
        pass
    finally:
        if old:
            subprocess.run(
                ["xclip", "-selection", "clipboard"],
                input=old, text=True, timeout=2,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )

    return None


def get_window_pid(wid: str) -> int | None:
    """Get PID of the process that owns the window."""
    output = _run(["xdotool", "getwindowpid", wid])
    if output:
        try:
            return int(output.strip())
        except ValueError:
            pass
    return None


# Extensions we consider as documents
_DOC_EXTENSIONS = frozenset(
    {".pdf", ".epub", ".txt", ".md", ".markdown", ".html", ".htm", ".rst", ".org", ".djvu"}
)


def get_document_from_pid(pid: int) -> str | None:
    """Get document file path from process info (cmdline + open file descriptors)."""
    # 1. Check command-line arguments — "okular /path/to/file.pdf"
    try:
        cmdline = Path(f"/proc/{pid}/cmdline").read_bytes()
        for arg in cmdline.split(b"\x00"):
            try:
                arg_str = arg.decode("utf-8", errors="ignore")
            except UnicodeDecodeError:
                continue
            if not arg_str:
                continue
            p = Path(arg_str)
            if p.suffix.lower() in _DOC_EXTENSIONS and p.is_file():
                return str(p.resolve())
    except OSError:
        pass

    # 2. Check open file descriptors — viewer keeps the fd open
    fd_dir = Path(f"/proc/{pid}/fd")
    try:
        for fd_path in fd_dir.iterdir():
            try:
                target = os.readlink(str(fd_path))
                if " (deleted)" in target:
                    continue
                p = Path(target)
                if p.suffix.lower() in _DOC_EXTENSIONS and p.is_file():
                    return str(p.resolve())
            except (OSError, ValueError):
                continue
    except OSError:
        pass

    return None


def get_document_path(title: str) -> str | None:
    """Extract file path from document viewer / editor window title."""
    # Real patterns from actual apps:
    #   "Clinical Psychology  — Okular"       (no extension!)
    #   "report.pdf — Evince Document Viewer"
    #   "Przxm.txt (~/Sync/PERZ) - Text Editor"
    #   "notes.md - Typora"

    # 1. Title with file extension + separator
    m = re.match(
        r"^([^\(—]+?\.(?:pdf|epub|txt|md|markdown|html?))\s*(?:\(.*?\))?\s*[—–\-]",
        title, re.IGNORECASE,
    )
    if m:
        path = m.group(1).strip()
        if path.startswith("~"):
            path = os.path.expanduser(path)
        return path

    # 2. Title with NO extension but ends with " — AppName" or " - AppName"
    #    e.g. "Clinical Psychology  — Okular"
    m = re.match(r"^(.+?)\s+[—–\-]\s+", title)
    if m:
        doc_name = m.group(1).strip()
        # Skip generic/app-like names
        if doc_name.lower() not in ("okular", "evince", "new document"):
            return doc_name

    # 3. Title that IS just a filename
    m = re.match(r"^([^\s]+?\.(?:pdf|epub|txt|md|markdown|html?))\s*$", title, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    return None


def get_editor_path(title: str) -> str | None:
    """Extract file path from text editor window title."""
    # GNOME Text Editor: "Przxm.txt (~/Sync/PERZ) - Text Editor"
    m = re.match(
        r"^(.+?\.(?:txt|md|markdown|html?|py|js|csv))\s*\((.+?)\)",
        title, re.IGNORECASE,
    )
    if m:
        filename = m.group(1).strip()
        directory = m.group(2).strip()
        if directory.startswith("~"):
            directory = os.path.expanduser(directory)
        full = os.path.join(directory, filename)
        if os.path.isfile(full):
            return full
        return filename

    # Typora: "notes.md - Typora"
    m = re.match(r"^(.+?\.(?:txt|md|markdown|html?|pdf|epub))\s*[—–\-]", title, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    return None


def find_file(filename: str) -> str | None:
    """Resolve a filename or document title to a full file path."""
    if os.path.isfile(filename):
        return filename

    # If the filename has an extension, search for it
    has_ext = bool(re.search(r"\.\w{1,5}$", filename, re.IGNORECASE))

    if has_ext:
        return _search_for_file(filename)

    # No extension — search with extensions appended
    for ext in (".pdf", ".epub", ".txt", ".md"):
        result = _search_for_file(filename + ext)
        if result:
            return result

    return None


def _search_for_file(filename: str) -> str | None:
    """Search for a file by name in recent files and common directories."""
    basename = os.path.basename(filename)

    # 1. GTK recently-used list (most reliable for recently opened files)
    recent_file = Path.home() / ".local/share/recently-used.xbel"
    if recent_file.exists():
        try:
            content = recent_file.read_text(errors="ignore")
            # Parse entries in reverse to get most recent first
            matches = list(re.finditer(r'href="([^"]+)"', content))
            for match in reversed(matches):
                candidate = match.group(1).removeprefix("file://")
                # URL-decode
                from urllib.parse import unquote
                candidate = unquote(candidate)
                if os.path.basename(candidate) == basename and Path(candidate).exists():
                    return candidate
        except OSError:
            pass

    # 2. Common directories (including common subdirectories)
    search_dirs = [
        Path.home() / "Documents",
        Path.home() / "Downloads",
        Path.home() / "Downloads" / "eBooks",
        Path.home() / "Desktop",
        Path.home() / "Sync",
        Path.home() / "Books",
        Path.home() / "Papers",
        Path.home() / "Library",
        Path("/tmp"),
    ]
    for d in search_dirs:
        if not d.exists():
            continue
        for f in d.rglob(basename):
            if f.is_file():
                return str(f)

    return None


# ── Application keywords ──────────────────────────────────────────
BROWSER_KEYWORDS = [
    "firefox", "chromium", "chrome", "google-chrome", "google-chrome-stable",
    "brave", "epiphany", "web", "vivaldi", "opera",
]

VIEWER_KEYWORDS = [
    "evince", "okular", "atril", "foliate", "calibre",
    "zathura", "mupdf", "xreader",
]

EDITOR_KEYWORDS = [
    "gedit", "gnome-text-editor", "kate", "pluma", "xed",
    "mousepad", "leafpad", "nvim", "vim", "emacs",
    "code", "sublime", "typora",
]


def main() -> None:
    wid = get_active_window_id()
    if not wid:
        sys.exit(1)

    wclass = get_window_class(wid)
    wtitle = get_window_title(wid)

    source = None

    # 1. Browser → extract URL from address bar
    if any(b in wclass for b in BROWSER_KEYWORDS):
        source = get_browser_url(wid)

    # 2. Document viewer → extract file from title
    if not source and any(v in wclass for v in VIEWER_KEYWORDS):
        path = get_document_path(wtitle)
        if path:
            source = find_file(path)

    # 3. Text editor → extract file from title
    if not source and any(e in wclass for e in EDITOR_KEYWORDS):
        path = get_editor_path(wtitle)
        if path:
            source = find_file(path)

    # 4. Fallback: check process info (cmdline + open file descriptors)
    if not source:
        pid = get_window_pid(wid)
        if pid:
            source = get_document_from_pid(pid)

    if source:
        print(source)
        sys.exit(0)

    sys.exit(1)


if __name__ == "__main__":
    main()
