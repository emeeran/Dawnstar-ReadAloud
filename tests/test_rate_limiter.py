"""Unit tests for _RateLimiter in core.engine module."""

import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.engine import _RateLimiter


class TestRateLimiter:

    def test_allows_up_to_max_calls(self):
        limiter = _RateLimiter(max_calls=3, window=1.0)
        for _ in range(3):
            limiter.acquire()

    def test_blocks_after_max_calls(self):
        limiter = _RateLimiter(max_calls=2, window=2.0)
        limiter.acquire()
        limiter.acquire()
        blocked = threading.Event()

        def try_acquire():
            limiter.acquire()
            blocked.set()

        t = threading.Thread(target=try_acquire, daemon=True)
        t.start()
        assert not blocked.wait(timeout=0.3)

    def test_allows_after_window_expires(self):
        limiter = _RateLimiter(max_calls=1, window=0.3)
        limiter.acquire()
        time.sleep(0.4)
        limiter.acquire()

    def test_thread_safety(self):
        limiter = _RateLimiter(max_calls=10, window=1.0)
        results = []
        errors = []

        def acquire_one():
            try:
                limiter.acquire()
                results.append(1)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=acquire_one) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)
        assert errors == []
        assert len(results) == 10
