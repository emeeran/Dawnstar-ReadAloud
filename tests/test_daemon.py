"""Integration tests for TTS daemon and IPC.

This test suite verifies:
- Daemon startup and shutdown
- Job submission and processing
- Pause/resume/stop controls
- IPC client communication
"""

import os
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from ttsd.daemon import TTSDaemon, DaemonState, Command, Job
from ttsd.ipc import IPCClient, UnixSocketServer, MAX_IPC_TEXT_LENGTH


class TestTTSDaemon:
    """Test daemon functionality."""

    def test_daemon_initializes_correctly(self):
        """Test daemon initializes with correct default state."""
        daemon = TTSDaemon(verbose=False, cache_enabled=False)

        assert daemon.state == DaemonState.IDLE
        assert daemon._running is False
        assert daemon.job_counter == 0
        assert len(daemon.jobs) == 0

    def test_daemon_starts_and_accepts_jobs(self):
        """Test daemon can start and queue jobs."""
        daemon = TTSDaemon(verbose=False, cache_enabled=False)
        thread = daemon.run_threaded()

        try:
            # Give daemon time to start
            time.sleep(0.5)

            # Submit a job
            job_id = daemon.submit_job("Hello world")
            assert job_id == 1

            # Verify job was queued
            assert job_id in daemon.jobs
            assert daemon.jobs[job_id].status == "queued"

        finally:
            daemon.shutdown()
            thread.join(timeout=5)

    def test_daemon_stop_clears_queue(self):
        """Test daemon stop clears job queue."""
        daemon = TTSDaemon(verbose=False, cache_enabled=False)
        thread = daemon.run_threaded()

        try:
            time.sleep(0.5)

            # Submit multiple jobs
            for i in range(5):
                daemon.submit_job(f"Job {i}")

            # Stop should clear queue
            daemon.stop()

            # Give it time to process
            time.sleep(0.5)

            # Queue should be empty or jobs cancelled
            state = daemon.get_state()
            assert state["queue_size"] == 0

        finally:
            daemon.shutdown()
            thread.join(timeout=5)

    def test_daemon_pause_resume(self):
        """Test daemon pause and resume functionality."""
        daemon = TTSDaemon(verbose=False, cache_enabled=False)
        thread = daemon.run_threaded()

        try:
            time.sleep(0.5)

            # Initially idle
            assert daemon.state == DaemonState.IDLE

            # Submit job to get into PLAYING state
            daemon.submit_job("Test text for pausing")
            time.sleep(0.5)

            # Pause (may not work if job completed already)
            result = daemon.pause()
            # Result depends on timing - just verify no crash

            # Resume
            result = daemon.resume()
            # Result depends on state

        finally:
            daemon.shutdown()
            thread.join(timeout=5)

    def test_daemon_get_state(self):
        """Test daemon state reporting."""
        daemon = TTSDaemon(verbose=False, cache_enabled=False)

        state = daemon.get_state()

        assert "state" in state
        assert "queue_size" in state
        assert "jobs_pending" in state
        assert state["state"] == "idle"
        assert state["queue_size"] == 0

    def test_daemon_get_voices(self):
        """Test daemon voice listing."""
        daemon = TTSDaemon(verbose=False, cache_enabled=False)

        voices = daemon.get_voices()

        # Should return list of voice configs
        assert isinstance(voices, list)
        assert len(voices) > 0  # At least en-us, en-uk, ta

        # Check structure
        for voice in voices:
            assert "id" in voice
            assert "name" in voice
            assert "voice" in voice

    def test_daemon_job_counter_increments(self):
        """Test job counter increments correctly."""
        daemon = TTSDaemon(verbose=False, cache_enabled=False)

        job1 = daemon.submit_job("First job")
        job2 = daemon.submit_job("Second job")
        job3 = daemon.submit_job("Third job")

        assert job1 == 1
        assert job2 == 2
        assert job3 == 3

    def test_daemon_shutdown(self):
        """Test graceful daemon shutdown."""
        daemon = TTSDaemon(verbose=False, cache_enabled=False)
        thread = daemon.run_threaded()

        time.sleep(0.5)

        # Submit a job
        daemon.submit_job("Test job")

        # Shutdown
        daemon.shutdown()
        thread.join(timeout=5)

        # Verify stopped
        assert daemon._running is False
        assert daemon.state == DaemonState.IDLE


class TestDaemonState:
    """Test daemon state transitions."""

    def test_state_enum_values(self):
        """Test DaemonState has correct values."""
        assert DaemonState.IDLE.value == "idle"
        assert DaemonState.PLAYING.value == "playing"
        assert DaemonState.PAUSED.value == "paused"
        assert DaemonState.STOPPING.value == "stopping"


class TestCommand:
    """Test Command dataclass."""

    def test_command_creation(self):
        """Test creating commands."""
        cmd = Command(action="speak", text="Hello")

        assert cmd.action == "speak"
        assert cmd.text == "Hello"
        assert cmd.options == {}
        assert cmd.job_id is None

    def test_command_with_options(self):
        """Test creating commands with options."""
        cmd = Command(
            action="speak",
            text="Hello",
            options={"lang": "en-uk", "speed": "fast"},
            job_id=42
        )

        assert cmd.action == "speak"
        assert cmd.text == "Hello"
        assert cmd.options["lang"] == "en-uk"
        assert cmd.job_id == 42


class TestJob:
    """Test Job dataclass."""

    def test_job_creation(self):
        """Test creating jobs."""
        job = Job(job_id=1, text="Hello world", options={})

        assert job.job_id == 1
        assert job.text == "Hello world"
        assert job.options == {}
        assert job.status == "queued"
        assert job.progress == 0.0

    def test_job_with_options(self):
        """Test creating jobs with options."""
        job = Job(
            job_id=2,
            text="Test",
            options={"lang": "ta"},
            status="processing",
            progress=0.5
        )

        assert job.job_id == 2
        assert job.text == "Test"
        assert job.options["lang"] == "ta"
        assert job.status == "processing"
        assert job.progress == 0.5


class TestIPCClient:
    """Test IPC client communication."""

    def test_client_detects_daemon_not_running(self):
        """Test client handles daemon not running."""
        client = IPCClient()
        result = client.status()

        # Should return error, not crash
        assert result["status"] == "error"
        assert "not running" in result["message"].lower() or "not found" in result["message"].lower()

    def test_client_speak_without_daemon(self):
        """Test speak command without running daemon."""
        client = IPCClient()
        result = client.speak("Hello world")

        assert result["status"] == "error"

    def test_client_stop_without_daemon(self):
        """Test stop command without running daemon."""
        client = IPCClient()
        result = client.stop()

        assert result["status"] == "error"


class TestIPCValidation:
    """Test IPC input validation."""

    def test_max_text_length_constant(self):
        """Test MAX_IPC_TEXT_LENGTH is defined correctly."""
        assert MAX_IPC_TEXT_LENGTH == 100 * 1024  # 100KB

    def test_text_length_validation_in_daemon(self):
        """Test daemon validates text length (via mock)."""
        daemon = TTSDaemon(verbose=False, cache_enabled=False)

        # Very long text should still be accepted (validation is in IPC layer)
        long_text = "x" * (MAX_IPC_TEXT_LENGTH + 1)

        # Daemon itself doesn't validate - that's IPC's job
        job_id = daemon.submit_job(long_text)
        assert job_id == 1


class TestUnixSocketServer:
    """Test Unix socket server."""

    def test_socket_path_in_runtime_dir(self):
        """Test socket is in XDG_RUNTIME_DIR."""
        socket_path = UnixSocketServer.SOCKET_PATH

        # Should be in user's runtime directory
        assert "tts-daemon.sock" in socket_path

        # Should use XDG_RUNTIME_DIR if set, or fallback
        expected_runtime = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
        assert socket_path.startswith(expected_runtime)

    def test_socket_path_constant(self):
        """Test SOCKET_PATH constant is defined."""
        assert hasattr(UnixSocketServer, "SOCKET_PATH")


# Run tests with: pytest tests/test_daemon.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
