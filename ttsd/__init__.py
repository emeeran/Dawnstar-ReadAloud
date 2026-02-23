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

from .daemon import TTSDaemon, DaemonState, Job, Command
from .ipc import UnixSocketServer, IPCClient

__all__ = [
    "TTSDaemon",
    "DaemonState",
    "Job",
    "Command",
    "UnixSocketServer",
    "IPCClient",
]
