"""
TTS Daemon D-Bus Service

Provides a standard D-Bus interface for the TTS daemon.
Bus: org.example.TTSDaemon
Path: /org/example/TTSDaemon

Methods:
- Speak(text: str, options: dict) -> int (job_id)
- SpeakSelection() -> int (job_id)
- Stop()
- Pause() -> bool
- Resume() -> bool
- GetState() -> dict
- GetVoices() -> array

Signals:
- StateChanged(state: str)
- JobCompleted(job_id: int, status: str)
- Progress(job_id: int, progress: float)
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Try to import pydbus
try:
    from pydbus import SessionBus
    from gi.repository import GLib
    DBUS_AVAILABLE = True
except ImportError:
    DBUS_AVAILABLE = False


DBUS_INTERFACE = """
<node>
    <interface name='org.example.TTSDaemon'>
        <method name='Speak'>
            <arg type='s' name='text' direction='in'/>
            <arg type='a{ss}' name='options' direction='in'/>
            <arg type='i' name='job_id' direction='out'/>
        </method>
        <method name='SpeakSelection'>
            <arg type='i' name='job_id' direction='out'/>
        </method>
        <method name='Stop'/>
        <method name='Pause'>
            <arg type='b' name='success' direction='out'/>
        </method>
        <method name='Resume'>
            <arg type='b' name='success' direction='out'/>
        </method>
        <method name='GetState'>
            <arg type='a{sv}' name='state' direction='out'/>
        </method>
        <method name='GetVoices'>
            <arg type='aa{ss}' name='voices' direction='out'/>
        </method>
        <signal name='StateChanged'>
            <arg type='s' name='state'/>
        </signal>
        <signal name='JobCompleted'>
            <arg type='i' name='job_id'/>
            <arg type='s' name='status'/>
        </signal>
        <signal name='Progress'>
            <arg type='i' name='job_id'/>
            <arg type='d' name='progress'/>
        </signal>
    </interface>
</node>
"""


class TTSDaemonDBus:
    """
    D-Bus interface for TTS daemon.

    This class is instantiated by pydbus and handles
    all D-Bus method calls by delegating to the daemon.
    """

    dbus = DBUS_INTERFACE

    def __init__(self, daemon):
        """
        Initialize D-Bus interface.

        Args:
            daemon: TTSDaemon instance to control
        """
        self.daemon = daemon
        self._bus: Optional[SessionBus] = None
        self._published = False

        # Wire up daemon callbacks to emit signals
        daemon.on_state_change = self._on_state_change
        daemon.on_job_complete = self._on_job_complete
        daemon.on_progress = self._on_progress

    def Speak(self, text: str, options: Dict[str, str]) -> int:
        """Queue text for speaking."""
        job_id = self.daemon.submit_job(text, options)
        return job_id

    def SpeakSelection(self) -> int:
        """Speak clipboard content."""
        sys.path.insert(0, str(Path(__file__).parent.parent))
        import tts_platform

        text = tts_platform.get_clipboard_text()
        if not text:
            return -1

        return self.daemon.submit_job(text, {})

    def Stop(self) -> None:
        """Stop playback and clear queue."""
        self.daemon.stop()

    def Pause(self) -> bool:
        """Pause playback."""
        return self.daemon.pause()

    def Resume(self) -> bool:
        """Resume playback."""
        return self.daemon.resume()

    def GetState(self) -> Dict[str, Any]:
        """Get current daemon state."""
        return self.daemon.get_state()

    def GetVoices(self) -> List[Dict[str, str]]:
        """Get available voices."""
        return self.daemon.get_voices()

    def _on_state_change(self, state) -> None:
        """Emit StateChanged signal."""
        self.StateChanged(state.value)

    def _on_job_complete(self, job) -> None:
        """Emit JobCompleted signal."""
        self.JobCompleted(job.job_id, job.status)

    def _on_progress(self, job_id: int, progress: float) -> None:
        """Emit Progress signal."""
        self.Progress(job_id, progress)

    # Signal emitters (called by pydbus)
    def StateChanged(self, state: str) -> None:
        pass

    def JobCompleted(self, job_id: int, status: str) -> None:
        pass

    def Progress(self, job_id: int, progress: float) -> None:
        pass

    def publish(self) -> bool:
        """Publish the D-Bus service."""
        if not DBUS_AVAILABLE:
            return False

        try:
            self._bus = SessionBus()
            self._bus.publish("org.example.TTSDaemon", self)
            self._published = True
            return True
        except Exception as e:
            print(f"Failed to publish D-Bus service: {e}")
            return False

    def unpublish(self) -> None:
        """Unpublish the D-Bus service."""
        if self._bus and self._published:
            # pydbus doesn't have explicit unpublish, but we can clear references
            self._published = False


def create_dbus_service(daemon) -> Optional[TTSDaemonDBus]:
    """
    Create and publish a D-Bus service for the daemon.

    Args:
        daemon: TTSDaemon instance

    Returns:
        TTSDaemonDBus instance if successful, None if D-Bus unavailable
    """
    if not DBUS_AVAILABLE:
        print("D-Bus support not available (install pydbus)")
        return None

    service = TTSDaemonDBus(daemon)
    if service.publish():
        print("D-Bus service published: org.example.TTSDaemon")
        return service

    return None


# D-Bus client for testing
class DBusClient:
    """Simple D-Bus client for the TTS daemon."""

    def __init__(self):
        if not DBUS_AVAILABLE:
            raise RuntimeError("D-Bus support not available")

        self.bus = SessionBus()

    @property
    def daemon(self):
        """Get proxy to the daemon."""
        return self.bus.get("org.example.TTSDaemon", "/org/example/TTSDaemon")

    def speak(self, text: str, options: Optional[Dict] = None) -> int:
        """Speak text."""
        return self.daemon.Speak(text, options or {})

    def stop(self) -> None:
        """Stop playback."""
        self.daemon.Stop()

    def pause(self) -> bool:
        """Pause playback."""
        return self.daemon.Pause()

    def resume(self) -> bool:
        """Resume playback."""
        return self.daemon.Resume()

    def get_state(self) -> Dict:
        """Get daemon state."""
        return self.daemon.GetState()

    def get_voices(self) -> List:
        """Get available voices."""
        return self.daemon.GetVoices()
