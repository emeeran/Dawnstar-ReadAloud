"""
TTS Daemon Module

Provides a background service for text-to-speech with:
- Unix socket IPC for fast local communication
- D-Bus interface for standard Linux integration
- Queue-based command processing
- Multi-engine fallback (Edge TTS → gTTS → espeak)
"""

from .daemon import TTSDaemon, DaemonState, Job, Command
from .ipc import UnixSocketServer, IPCClient

try:
    from .dbus_service import TTSDaemonDBus, DBusClient, create_dbus_service, DBUS_AVAILABLE
except ImportError:
    DBUS_AVAILABLE = False
    TTSDaemonDBus = None
    DBusClient = None
    create_dbus_service = None

__all__ = [
    "TTSDaemon",
    "DaemonState",
    "Job",
    "Command",
    "UnixSocketServer",
    "IPCClient",
    "TTSDaemonDBus",
    "DBusClient",
    "create_dbus_service",
    "DBUS_AVAILABLE",
]
