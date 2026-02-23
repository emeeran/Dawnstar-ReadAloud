"""
TTS Daemon IPC Module

Unix socket-based inter-process communication with JSON protocol.
Provides fast local communication between clients and the TTS daemon.
"""

import os
import json
import socket
import threading
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, Callable


class UnixSocketServer:
    """
    Unix socket server for daemon communication.

    Protocol: JSON messages terminated by newline
    Request: {"cmd": "speak", "text": "...", "options": {...}}
    Response: {"status": "ok", "job_id": 1} or {"status": "error", "message": "..."}
    """

    SOCKET_PATH = os.environ.get(
        "XDG_RUNTIME_DIR",
        f"/run/user/{os.getuid()}"
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
        self.server_socket: Optional[socket.socket] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the IPC server."""
        # Remove stale socket file
        if self.socket_path.exists():
            self.socket_path.unlink()

        # Ensure directory exists
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)

        # Create Unix socket
        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(str(self.socket_path))
        self.server_socket.listen(5)
        self.server_socket.settimeout(1.0)

        self._running = True

        while self._running:
            try:
                client, _ = self.server_socket.accept()
                thread = threading.Thread(
                    target=self._handle_client,
                    args=(client,),
                    daemon=True
                )
                thread.start()
            except socket.timeout:
                continue
            except Exception:
                if self._running:
                    continue
                break

    def stop(self) -> None:
        """Stop the IPC server."""
        self._running = False
        if self.server_socket:
            self.server_socket.close()
        if self.socket_path.exists():
            self.socket_path.unlink()

    def _handle_client(self, client: socket.socket) -> None:
        """Handle a client connection."""
        buffer = ""

        try:
            while self._running:
                data = client.recv(self.BUFFER_SIZE)
                if not data:
                    break

                buffer += data.decode("utf-8")

                # Process complete messages (newline-delimited JSON)
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if not line.strip():
                        continue

                    try:
                        request = json.loads(line)
                        response = self._process_command(request)
                    except json.JSONDecodeError as e:
                        response = {"status": "error", "message": f"Invalid JSON: {e}"}

                    client.send((json.dumps(response) + "\n").encode("utf-8"))

        except Exception as e:
            pass
        finally:
            client.close()

    def _process_command(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a command and return response."""
        cmd = request.get("cmd", "").lower()

        try:
            if cmd == "speak":
                text = request.get("text", "")
                options = request.get("options", {})
                if not text:
                    return {"status": "error", "message": "No text provided"}

                job_id = self.daemon.submit_job(text, options)
                return {"status": "ok", "job_id": job_id}

            elif cmd == "speak-selection":
                import sys
                sys.path.insert(0, str(Path(__file__).parent.parent))
                import tts_platform

                text = tts_platform.get_clipboard_text()
                if not text:
                    return {"status": "error", "message": "No text in clipboard"}

                job_id = self.daemon.submit_job(text, request.get("options", {}))
                return {"status": "ok", "job_id": job_id}

            elif cmd == "stop":
                self.daemon.stop()
                return {"status": "ok"}

            elif cmd == "pause":
                if self.daemon.pause():
                    return {"status": "ok", "state": "paused"}
                return {"status": "error", "message": "Cannot pause in current state"}

            elif cmd == "resume":
                if self.daemon.resume():
                    return {"status": "ok", "state": "playing"}
                return {"status": "error", "message": "Cannot resume in current state"}

            elif cmd == "status" or cmd == "get-state":
                state = self.daemon.get_state()
                return {"status": "ok", "data": state}

            elif cmd == "get-voices":
                voices = self.daemon.get_voices()
                return {"status": "ok", "voices": voices}

            elif cmd == "shutdown":
                self.daemon.shutdown()
                return {"status": "ok", "message": "Shutting down"}

            else:
                return {"status": "error", "message": f"Unknown command: {cmd}"}

        except Exception as e:
            return {"status": "error", "message": str(e)}


class IPCClient:
    """
    Client for communicating with the TTS daemon via Unix socket.
    """

    SOCKET_PATH = UnixSocketServer.SOCKET_PATH
    TIMEOUT = 5.0

    def __init__(self, socket_path: Optional[str] = None):
        self.socket_path = socket_path or self.SOCKET_PATH

    def _send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
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

    def speak(self, text: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Queue text for speaking."""
        return self._send_command({
            "cmd": "speak",
            "text": text,
            "options": options or {}
        })

    def speak_selection(self, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Speak clipboard content."""
        return self._send_command({
            "cmd": "speak-selection",
            "options": options or {}
        })

    def stop(self) -> Dict[str, Any]:
        """Stop playback and clear queue."""
        return self._send_command({"cmd": "stop"})

    def pause(self) -> Dict[str, Any]:
        """Pause playback."""
        return self._send_command({"cmd": "pause"})

    def resume(self) -> Dict[str, Any]:
        """Resume playback."""
        return self._send_command({"cmd": "resume"})

    def status(self) -> Dict[str, Any]:
        """Get daemon status."""
        return self._send_command({"cmd": "status"})

    def get_voices(self) -> Dict[str, Any]:
        """Get available voices."""
        return self._send_command({"cmd": "get-voices"})

    def is_running(self) -> bool:
        """Check if daemon is running."""
        result = self._send_command({"cmd": "status"})
        return result.get("status") == "ok"

    def shutdown(self) -> Dict[str, Any]:
        """Shutdown the daemon."""
        return self._send_command({"cmd": "shutdown"})
