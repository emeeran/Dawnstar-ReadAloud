"""
TTS Daemon Core

Main daemon loop with queue-based processing, state management,
and multi-engine TTS generation. Optional component for low-latency
speech synthesis.
"""

import contextlib
import os
import queue
import signal
import subprocess
import sys
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

# Import from parent module
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import (
    LANG_CONFIG,
    AudioPlayer,
    ContentExtractor,
    EngineError,
    PlaybackError,
    TTSConfig,
    TTSEngine,
)

from . import SOCKET_PATH


class DaemonState(Enum):
    """Daemon operational states."""

    IDLE = "idle"
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPING = "stopping"


@dataclass
class Command:
    """Command sent to the daemon."""

    action: str
    text: str | None = None
    options: dict[str, Any] = field(default_factory=dict)
    job_id: int | None = None


@dataclass
class Job:
    """TTS job in the queue."""

    job_id: int
    text: str
    options: dict[str, Any]
    status: str = "queued"
    progress: float = 0.0


class TTSDaemon:
    """
    Text-to-Speech daemon with queue-based processing.

    Features:
    - FIFO command queue
    - State management (idle/playing/paused)
    - Pause/Resume/Stop controls
    - Progress callbacks
    - Multi-engine fallback

    Usage:
        # Start daemon
        daemon = TTSDaemon()
        daemon.run()  # Blocking

        # Or in thread
        thread = daemon.run_threaded()

        # Submit jobs
        job_id = daemon.submit_job("Hello world")

        # Control playback
        daemon.pause()
        daemon.resume()
        daemon.stop()
    """

    SOCKET_PATH = SOCKET_PATH

    # Maximum number of completed jobs to keep in history
    MAX_JOB_HISTORY = 100

    def __init__(
        self,
        lang: str = "en-us",
        speed: str = "normal",
        cache_enabled: bool = True,
        verbose: bool = False,
    ):
        self.config = TTSConfig(lang, cache_enabled, verbose, speed)
        self.state = DaemonState.IDLE
        self.command_queue: queue.Queue[Command] = queue.Queue()
        self.jobs: dict[int, Job] = {}
        self.job_counter = 0
        self.current_job: Job | None = None

        self._running = False
        self._pause_event = threading.Event()
        self._pause_event.set()  # Not paused by default
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # Callbacks
        self.on_state_change: Callable[[DaemonState], None] | None = None
        self.on_job_complete: Callable[[Job], None] | None = None
        self.on_progress: Callable[[int, float], None] | None = None

        # Pre-initialize TTS engine for low latency
        self.engine = TTSEngine(self.config)

    def _set_state(self, new_state: DaemonState) -> None:
        """Update daemon state and trigger callback."""
        with self._lock:
            if self.state != new_state:
                self.state = new_state
                if self.on_state_change:
                    self.on_state_change(new_state)

    def submit_job(self, text: str, options: dict[str, Any] | None = None) -> int:
        """Submit a new TTS job to the queue."""
        with self._lock:
            self.job_counter += 1
            job_id = self.job_counter

        job = Job(job_id=job_id, text=text, options=options or {})
        self.jobs[job_id] = job

        cmd = Command(
            action="speak", text=text, options=options or {}, job_id=job_id
        )
        self.command_queue.put(cmd)

        return job_id

    def stop(self) -> None:
        """Stop current playback and clear queue."""
        self._stop_event.set()
        self._set_state(DaemonState.STOPPING)

        # Clear queue
        while not self.command_queue.empty():
            try:
                self.command_queue.get_nowait()
            except queue.Empty:
                break

        # Kill audio playback
        self._kill_playback()

        self._set_state(DaemonState.IDLE)
        self._stop_event.clear()

    def pause(self) -> bool:
        """Pause current playback."""
        if self.state == DaemonState.PLAYING:
            self._pause_event.clear()
            self._set_state(DaemonState.PAUSED)
            return True
        return False

    def resume(self) -> bool:
        """Resume paused playback."""
        if self.state == DaemonState.PAUSED:
            self._pause_event.set()
            self._set_state(DaemonState.PLAYING)
            return True
        return False

    def get_state(self) -> dict[str, Any]:
        """Get current daemon state."""
        with self._lock:
            state_info = {
                "state": self.state.value,
                "queue_size": self.command_queue.qsize(),
                "current_job": None,
                "jobs_pending": len(
                    [j for j in self.jobs.values() if j.status == "queued"]
                ),
            }

            if self.current_job:
                state_info["current_job"] = {
                    "job_id": self.current_job.job_id,
                    "text_preview": self.current_job.text[:100],
                    "progress": self.current_job.progress,
                }

            return state_info

    def get_voices(self) -> list:
        """Get available voices."""
        return [
            {"id": lang_id, "name": cfg["name"], "voice": cfg["voice"]}
            for lang_id, cfg in LANG_CONFIG.items()
        ]

    def _kill_playback(self) -> None:
        """Kill any active audio playback.

        Uses -x flag for exact process name matching to avoid killing
        unrelated processes that happen to contain the player name in
        their command line.
        """
        for player in ["mpg123", "cvlc", "ffplay", "aplay", "paplay"]:
            with contextlib.suppress(OSError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
                subprocess.run(
                    ["pkill", "-x", player],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=2,
                )

    def _process_job(self, job: Job) -> bool:
        """Process a single TTS job.

        Args:
            job: The job to process.

        Returns:
            True if job completed successfully, False otherwise.
        """
        job.status = "processing"
        self.current_job = job

        try:
            # Clean and chunk text
            clean_text = ContentExtractor.clean_text(job.text)
            chunks = ContentExtractor.chunk_text(clean_text)

            total_chunks = len(chunks)

            for i, chunk in enumerate(chunks):
                if self._stop_event.is_set():
                    job.status = "cancelled"
                    return False

                # Wait if paused
                self._pause_event.wait()

                if self._stop_event.is_set():
                    job.status = "cancelled"
                    return False

                # Generate audio
                audio = self.engine.generate(chunk)
                if not audio:
                    job.status = "error"
                    job.progress = (i + 1) / total_chunks
                    return False

                # Update progress
                job.progress = (i + 1) / total_chunks
                if self.on_progress:
                    self.on_progress(job.job_id, job.progress)

                # Play audio
                self._set_state(DaemonState.PLAYING)
                if not AudioPlayer.play(audio, self.config):
                    job.status = "error"
                    return False

            job.status = "completed"
            job.progress = 1.0
            return True

        except (EngineError, PlaybackError, OSError, RuntimeError) as e:
            job.status = f"error: {str(e)}"
            return False
        except Exception as e:
            # Catch-all for unexpected errors, but log them properly
            job.status = f"error: {str(e)}"
            if self.config.verbose:
                print(f"Unexpected error in job {job.job_id}: {type(e).__name__}: {e}")
            return False
        finally:
            if self.on_job_complete:
                self.on_job_complete(job)
            self.current_job = None
            self._cleanup_jobs()

    def run(self) -> None:
        """Main daemon loop (blocking)."""
        self._running = True
        self._set_state(DaemonState.IDLE)

        # Handle signals (only in main thread)
        try:
            signal.signal(signal.SIGTERM, lambda *_: self.shutdown())
            signal.signal(signal.SIGINT, lambda *_: self.shutdown())
        except ValueError:
            # Signal handling only works in main thread
            pass

        while self._running:
            try:
                # Wait for command with timeout
                try:
                    cmd = self.command_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                if cmd.action == "speak":
                    job = self.jobs.get(cmd.job_id)
                    if job:
                        self._process_job(job)
                    self._set_state(DaemonState.IDLE)

                elif cmd.action == "stop":
                    self.stop()

                elif cmd.action == "pause":
                    self.pause()

                elif cmd.action == "resume":
                    self.resume()

                elif cmd.action == "shutdown":
                    self._running = False

            except (queue.Empty, KeyboardInterrupt):
                continue
            except (OSError, RuntimeError) as e:
                if self.config.verbose:
                    print(f"Daemon error: {e}")
            except Exception as e:
                # Log unexpected errors but keep daemon running
                if self.config.verbose:
                    print(f"Unexpected daemon error: {type(e).__name__}: {e}")

    def _cleanup_jobs(self) -> None:
        """Remove old completed jobs to prevent unbounded memory growth."""
        completed_ids = [
            jid for jid, job in self.jobs.items()
            if job.status in ("completed", "cancelled")
        ]
        if len(completed_ids) > self.MAX_JOB_HISTORY:
            # Remove oldest completed jobs beyond the limit
            completed_ids.sort()
            for jid in completed_ids[:-self.MAX_JOB_HISTORY]:
                del self.jobs[jid]

    def shutdown(self) -> None:
        """Gracefully shutdown the daemon."""
        self._running = False
        self.stop()

        # Remove socket file
        socket_path = Path(self.SOCKET_PATH)
        if socket_path.exists():
            socket_path.unlink()

    def run_threaded(self) -> threading.Thread:
        """Run daemon in a background thread."""
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        return thread


def main():
    """Entry point for running daemon directly."""
    import argparse

    parser = argparse.ArgumentParser(description="TTS Daemon")
    parser.add_argument("--lang", default="en-us", help="Default language")
    parser.add_argument(
        "--speed", default="normal", choices=["slow", "normal", "fast"]
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()

    daemon = TTSDaemon(
        lang=args.lang,
        speed=args.speed,
        verbose=args.verbose,
        cache_enabled=not args.no_cache,
    )

    # Set up IPC
    from .ipc import UnixSocketServer

    ipc_server = UnixSocketServer(daemon)

    print(f"TTS Daemon starting on {daemon.SOCKET_PATH}")

    # Run IPC in thread
    ipc_thread = threading.Thread(target=ipc_server.start, daemon=True)
    ipc_thread.start()

    # Run daemon main loop
    try:
        daemon.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
        daemon.shutdown()
        ipc_server.stop()


if __name__ == "__main__":
    main()
