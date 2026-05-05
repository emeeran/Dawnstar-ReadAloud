"""
TTS Daemon Module

Optional background service for text-to-speech with:
- Unix socket IPC for fast local communication
- Queue-based command processing
- Low latency (~50ms vs ~500ms for CLI mode)

Usage:
    # Start daemon from command line
    python -m ttsd --daemon

    # Or programmatically
    from ttsd import TTSDaemon, IPCClient

    daemon = TTSDaemon()
    daemon.run_threaded()

    client = IPCClient()
    client.speak("Hello world")
"""

import os
from pathlib import Path

# Shared socket path — defined once, used by both daemon and IPC
SOCKET_PATH = os.environ.get(
    "XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"
) + "/tts-daemon.sock"

from .daemon import Command, DaemonState, Job, TTSDaemon
from .ipc import IPCClient, UnixSocketServer

__all__ = [
    "TTSDaemon",
    "DaemonState",
    "Job",
    "Command",
    "UnixSocketServer",
    "IPCClient",
    "SOCKET_PATH",
]
