"""
TTS Daemon IPC Module

Unix socket-based inter-process communication with JSON protocol.
Provides fast local communication between clients and the TTS daemon.

Security features:
- Restrictive socket permissions (owner-only access)
- Maximum message size validation (DoS prevention)
- Input length limits on text fields
"""

import asyncio
import json
import os
import socket
from pathlib import Path
from typing import Any

from . import SOCKET_PATH as _SHARED_SOCKET_PATH

# Security: Maximum text length for IPC requests (100KB)
MAX_IPC_TEXT_LENGTH = 100 * 1024

# Security: Maximum message size for JSON requests (1MB)
MAX_MESSAGE_SIZE = 1024 * 1024


class UnixSocketServer:
    """
    Unix socket server for daemon communication.

    Protocol: JSON messages terminated by newline
    Request: {"cmd": "speak", "text": "...", "options": {...}}
    Response: {"status": "ok", "job_id": 1} or {"status": "error", "message": "..."}

    Security:
        - Socket file created with 0600 permissions (owner-only)
        - Message size limited to prevent DoS attacks
    """

    SOCKET_PATH = _SHARED_SOCKET_PATH

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

        # SECURITY: Set restrictive umask before creating socket
        # This ensures the socket file is created with 0600 permissions
        old_umask = os.umask(0o077)
        try:
            self._loop = asyncio.get_running_loop()
            self._shutdown_event = asyncio.Event()
            self.server = await asyncio.start_unix_server(
                self._handle_client,
                path=str(self.socket_path),
                limit=self.BUFFER_SIZE,
            )

            # SECURITY: Explicitly set socket permissions after creation
            # (umask may not be sufficient on all systems)
            import contextlib
            with contextlib.suppress(OSError):
                os.chmod(self.socket_path, 0o600)

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
        finally:
            # Restore original umask
            os.umask(old_umask)

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
                # SECURITY: Read with size limit to prevent DoS
                data = await reader.readline()
                if not data:
                    break

                # SECURITY: Check message size before processing
                if len(data) > MAX_MESSAGE_SIZE:
                    response = {
                        "status": "error",
                        "message": f"Message too large (max {MAX_MESSAGE_SIZE} bytes)"
                    }
                    writer.write((json.dumps(response) + "\n").encode("utf-8"))
                    await writer.drain()
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

                    # SECURITY: Validate text length
                    if not text:
                        return {"status": "error", "message": "No text provided"}
                    if len(text) > MAX_IPC_TEXT_LENGTH:
                        return {
                            "status": "error",
                            "message": f"Text too long (max {MAX_IPC_TEXT_LENGTH} bytes)"
                        }

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

        except (OSError, RuntimeError, ValueError, KeyError) as e:
            return {"status": "error", "message": str(e)}
        except Exception:
            # Catch-all for unexpected errors — use generic message
            # to avoid leaking internal details to IPC clients
            return {"status": "error", "message": "Internal error"}


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

    SOCKET_PATH = _SHARED_SOCKET_PATH
    TIMEOUT = 5.0

    def __init__(self, socket_path: str | None = None):
        """
        Initialize IPC client.

        Args:
            socket_path: Path to Unix socket (default: auto-detect)
        """
        self.socket_path = socket_path or self.SOCKET_PATH

    def _send_command(self, command: dict[str, Any]) -> dict[str, Any]:
        """Send a command to the daemon and return response.

        Args:
            command: Command dictionary with 'cmd' key.

        Returns:
            Response dictionary with 'status' key.
        """
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
        """Queue text for speaking.

        Args:
            text: Text to speak.
            options: Optional TTS options (language, speed, etc.).

        Returns:
            Response with job_id on success, error on failure.
        """
        return self._send_command(
            {"cmd": "speak", "text": text, "options": options or {}}
        )

    def speak_selection(self, options: dict[str, Any] | None = None) -> dict[str, Any]:
        """Speak clipboard content.

        Args:
            options: Optional TTS options.

        Returns:
            Response with job_id on success, error on failure.
        """
        return self._send_command({"cmd": "speak-selection", "options": options or {}})

    def stop(self) -> dict[str, Any]:
        """Stop playback and clear queue.

        Returns:
            Response indicating success or failure.
        """
        return self._send_command({"cmd": "stop"})

    def pause(self) -> dict[str, Any]:
        """Pause playback.

        Returns:
            Response indicating success or failure.
        """
        return self._send_command({"cmd": "pause"})

    def resume(self) -> dict[str, Any]:
        """Resume playback.

        Returns:
            Response indicating success or failure.
        """
        return self._send_command({"cmd": "resume"})

    def status(self) -> dict[str, Any]:
        """Get daemon status.

        Returns:
            Dictionary with state, queue_size, and current_job info.
        """
        return self._send_command({"cmd": "status"})

    def get_voices(self) -> dict[str, Any]:
        """Get available voices.

        Returns:
            List of available voice configurations.
        """
        return self._send_command({"cmd": "get-voices"})

    def is_running(self) -> bool:
        """Check if daemon is running.

        Returns:
            True if daemon is responding, False otherwise.
        """
        result = self._send_command({"cmd": "status"})
        return result.get("status") == "ok"

    def shutdown(self) -> dict[str, Any]:
        """Shutdown the daemon.

        Returns:
            Response indicating shutdown status.
        """
        return self._send_command({"cmd": "shutdown"})
