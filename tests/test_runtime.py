"""Unit tests for core.runtime module."""

import sys
import tempfile
import threading
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.runtime import CacheManager, NotificationManager


class TestCacheManagerInitialize:

    def setup_method(self):
        CacheManager._initialized = False
        CacheManager._max_size_bytes = 500 * 1024 * 1024

    def test_sets_max_size(self):
        CacheManager.initialize(max_size_mb=100)
        assert CacheManager._max_size_bytes == 100 * 1024 * 1024
        assert CacheManager._initialized is True

    def test_idempotent(self):
        CacheManager.initialize(max_size_mb=200)
        CacheManager.initialize(max_size_mb=50)
        assert CacheManager._max_size_bytes == 200 * 1024 * 1024

    def test_default_size(self):
        CacheManager.initialize()
        assert CacheManager._max_size_bytes == 500 * 1024 * 1024


class TestCacheManagerGetStats:

    def setup_method(self):
        CacheManager._initialized = False

    def test_empty_when_dir_missing(self):
        with patch.object(Path, "exists", return_value=False):
            stats = CacheManager.get_cache_stats()
        assert stats["files"] == 0
        assert stats["size_mb"] == 0.0

    def test_returns_expected_keys(self):
        stats = CacheManager.get_cache_stats()
        for key in ("files", "size_bytes", "size_mb", "max_size_mb"):
            assert key in stats

    def test_counts_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(3):
                (Path(tmpdir) / f"f{i}.mp3").write_bytes(b"x" * 100)
            with patch("core.runtime.CACHE_DIR", Path(tmpdir)):
                stats = CacheManager.get_cache_stats()
            assert stats["files"] == 3
            assert stats["size_bytes"] == 300


class TestCacheManagerEnforceLimit:

    def setup_method(self):
        CacheManager._initialized = False

    def test_noop_on_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir, patch("core.runtime.CACHE_DIR", Path(tmpdir)):
            CacheManager._enforce_limit()

    def test_removes_oldest_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files larger than 500-byte limit
            for i in range(5):
                p = Path(tmpdir) / f"f{i}.mp3"
                p.write_bytes(b"x" * 200)
            CacheManager._initialized = True
            CacheManager._max_size_bytes = 500
            with patch("core.runtime.CACHE_DIR", Path(tmpdir)):
                CacheManager._enforce_limit()
                remaining = list(Path(tmpdir).glob("*.mp3"))
            assert len(remaining) <= 2


class TestCacheManagerClear:

    def setup_method(self):
        CacheManager._initialized = False

    def test_clear_nonexistent_dir(self):
        with patch("core.runtime.CACHE_DIR", Path("/nonexistent")):
            assert CacheManager.clear() == 0

    def test_clear_removes_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "a.mp3").write_bytes(b"data")
            (Path(tmpdir) / "b.mp3").write_bytes(b"data")
            with patch("core.runtime.CACHE_DIR", Path(tmpdir)):
                assert CacheManager.clear() == 2

    def test_clear_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir, patch("core.runtime.CACHE_DIR", Path(tmpdir)):
            assert CacheManager.clear() == 0


class TestCacheManagerThreadSafety:

    def test_concurrent_clear(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(10):
                (Path(tmpdir) / f"f{i}.mp3").write_bytes(b"data")
            with patch("core.runtime.CACHE_DIR", Path(tmpdir)):
                errors = []

                def clear():
                    try:
                        CacheManager.clear()
                    except Exception as e:
                        errors.append(e)

                threads = [threading.Thread(target=clear) for _ in range(5)]
                for t in threads:
                    t.start()
                for t in threads:
                    t.join()
                assert errors == []


class TestNotificationManagerSetEnabled:

    def test_enable_disable(self):
        NotificationManager.set_enabled(False)
        assert NotificationManager._enabled is False
        NotificationManager.set_enabled(True)
        assert NotificationManager._enabled is True


class TestNotificationManagerIsAvailable:

    @patch("shutil.which")
    def test_available(self, mock_which):
        mock_which.return_value = "/usr/bin/notify-send"
        NotificationManager._available = None
        assert NotificationManager.is_available() is True

    @patch("shutil.which")
    def test_unavailable(self, mock_which):
        mock_which.return_value = None
        NotificationManager._available = None
        assert NotificationManager.is_available() is False


class TestNotificationManagerNotify:

    def test_returns_false_when_disabled(self):
        NotificationManager.set_enabled(False)
        assert NotificationManager.notify("T", "M") is False
        NotificationManager.set_enabled(True)

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_sends_when_enabled(self, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/notify-send"
        NotificationManager._available = None
        NotificationManager.set_enabled(True)
        assert NotificationManager.notify("Title", "Msg") is True
        mock_run.assert_called_once()

    @patch("subprocess.run", side_effect=OSError("fail"))
    @patch("shutil.which")
    def test_handles_error(self, mock_which, _mock_run):
        mock_which.return_value = "/usr/bin/notify-send"
        NotificationManager._available = None
        NotificationManager.set_enabled(True)
        assert NotificationManager.notify("T", "M") is False
