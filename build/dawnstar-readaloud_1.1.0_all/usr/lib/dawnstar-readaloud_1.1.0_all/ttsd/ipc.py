"""
TTS Daemon IPC Module

Unix socket-based inter-process communication with JSON protocol.
Provides fast local communication between clients and the TTS daemon.
"""

import asyncio
import json
import os
import socket
from pathlib import Path
from typing import Any


class UnixSocketServer:
    """
    Unix socket server for daemon communication.

    Protocol: JSON messages terminated by newline
    Request: {"cmd": "speak", "text": "...", "options": {...}}
    Response: {"status": "ok", "job_id": 1} or {"status": "error", "message": "..."}
    """

    SOCKET_PATH = os.environ.get(
        "XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"
    ) + "/tts-daemon.sock"

    BUFFER_SIZE = 65536

    def __init__(self, daemon):
        """
        Initialize IPC server.

        Args:
            daemon: TTSDaemon instance to control
        """
        self.daemon = daemon
        self.socket_path = Path(self.SOCKET_PATH)
        self.server: asyncio.AbstractServer | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._shutdown_event: asyncio.Event | None = None
        self._running = False

    def start(self) -> None:
        """Start the IPC server (blocking)."""
        asyncio.run(self._serve())

    async def _serve(self) -> None:
        """Run asyncio Unix socket server until shutdown is requested."""
        # Remove stale socket file
        if self.socket_path.exists():
            self.socket_path.unlink()

        # Ensure directory exists
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)

        self._loop = asyncio.get_running_loop()
        self._shutdown_event = asyncio.Event()
        self.server = await asyncio.start_unix_server(
            self._handle_client,
            path=str(self.socket_path),
            limit=self.BUFFER_SIZE,
        )

        self._running = True
        await self._shutdown_event.wait()

        if self.server is not None:
            self.server.close()
            await self.server.wait_closed()

        if self.socket_path.exists():
            self.socket_path.unlink()

        self.server = None
        self._loop = None
        self._shutdown_event = None

    def stop(self) -> None:
        """Stop the IPC server."""
        self._running = False
        if self._loop and self._shutdown_event:
            self._loop.call_soon_threadsafe(self._shutdown_event.set)
        elif self.socket_path.exists():
            self.socket_path.unlink()

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """Handle a single client connection."""
        try:
            while self._running:
                data = await reader.readline()
                if not data:
                    break

                line = data.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                try:
                    request = json.loads(line)
                    response = self._process_command(request)
                except json.JSONDecodeError as e:
                    response = {"status": "error", "message": f"Invalid JSON: {e}"}

                writer.write((json.dumps(response) + "\n").encode("utf-8"))
                await writer.drain()
        except (ConnectionError, OSError):
            pass
        finally:
            writer.close()
            await writer.wait_closed()

    def _process_command(self, request: dict[str, Any]) -> dict[str, Any]:
        """Process a command and return response."""
        cmd = request.get("cmd", "").lower()

        try:
            match cmd:
                case "speak":
                    text = request.get("text", "")
                    options = request.get("options", {})
                    if not text:
                        return {"status": "error", "message": "No text provided"}

                    job_id = self.daemon.submit_job(text, options)
                    return {"status": "ok", "job_id": job_id}

                case "speak-selection":
                    from core.platform import get_clipboard_text

                    text = get_clipboard_text()
                    if not text:
                        return {"status": "error", "message": "No text in clipboard"}

                    job_id = self.daemon.submit_job(text, request.get("options", {}))
                    return {"status": "ok", "job_id": job_id}

                case "stop":
                    self.daemon.stop()
                    return {"status": "ok"}

                case "pause":
                    if self.daemon.pause():
                        return {"status": "ok", "state": "paused"}
                    return {"status": "error", "message": "Cannot pause in current state"}

                case "resume":
                    if self.daemon.resume():
                        return {"status": "ok", "state": "playing"}
                    return {"status": "error", "message": "Cannot resume in current state"}

                case "status" | "get-state":
                    state = self.daemon.get_state()
                    return {"status": "ok", "data": state}

                case "get-voices":
                    voices = self.daemon.get_voices()
                    return {"status": "ok", "voices": voices}

                case "shutdown":
                    self.daemon.shutdown()
                    return {"status": "ok", "message": "Shutting down"}

                case _:
                    return {"status": "error", "message": f"Unknown command: {cmd}"}

        except Exception as e:
            return {"status": "error", "message": str(e)}


class IPCClient:
    """
    Client for communicating with the TTS daemon via Unix socket.

    Usage:
        client = IPCClient()

        # Speak text
        result = client.speak("Hello world")

        # Speak clipboard
        result = client.speak_selection()

        # Control playback
        client.pause()
        client.resume()
        client.stop()

        # Check status
        status = client.status()
        if client.is_running():
            print("Daemon is running")
    """

    SOCKET_PATH = UnixSocketServer.SOCKET_PATH
    TIMEOUT = 5.0

    def __init__(self, socket_path: str | None = None):
        self.socket_path = socket_path or self.SOCKET_PATH

    def _send_command(self, command: dict[str, Any]) -> dict[str, Any]:
        """Send a command to the daemon and return response."""
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.TIMEOUT)

        try:
            sock.connect(self.socket_path)
            sock.send((json.dumps(command) + "\n").encode("utf-8"))

            response = sock.recv(65536).decode("utf-8")
            return json.loads(response.strip())

        except ConnectionRefusedError:
            return {"status": "error", "message": "Daemon not running"}
        except TimeoutError:
            return {"status": "error", "message": "Connection timeout"}
        except FileNotFoundError:
            return {"status": "error", "message": "Daemon socket not found"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            sock.close()

    def speak(self, text: str, options: dict[str, Any] | None = None) -> dict[str, Any]:
        """Queue text for speaking."""
        return self._send_command(
            {"cmd": "speak", "text": text, "options": options or {}}
        )

    def speak_selection(self, options: dict[str, Any] | None = None) -> dict[str, Any]:
        """Speak clipboard content."""
        return self._send_command({"cmd": "speak-selection", "options": options or {}})

    def stop(self) -> dict[str, Any]:
        """Stop playback and clear queue."""
        return self._send_command({"cmd": "stop"})

    def pause(self) -> dict[str, Any]:
        """Pause playback."""
        return self._send_command({"cmd": "pause"})

    def resume(self) -> dict[str, Any]:
        """Resume playback."""
        return self._send_command({"cmd": "resume"})

    def status(self) -> dict[str, Any]:
        """Get daemon status."""
        return self._send_command({"cmd": "status"})

    def get_voices(self) -> dict[str, Any]:
        """Get available voices."""
        return self._send_command({"cmd": "get-voices"})

    def is_running(self) -> bool:
        """Check if daemon is running."""
        result = self._send_command({"cmd": "status"})
        return result.get("status") == "ok"

    def shutdown(self) -> dict[str, Any]:
        """Shutdown the daemon."""
        return self._send_command({"cmd": "shutdown"})
