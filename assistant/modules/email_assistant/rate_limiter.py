"""
Rate Limiter for Gmail API
==========================
Token bucket rate limiter to stay within Gmail API quotas.
"""

import time
from collections import deque
from threading import Lock


class RateLimiter:
    """Token bucket rate limiter"""

    def __init__(self, max_calls: int = 100, period: int = 60):
        """
        Args:
            max_calls: Maximum calls allowed per period
            period: Time period in seconds (default 60 = 1 minute)
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()
        self.lock = Lock()

    def wait_if_needed(self):
        """Block if rate limit would be exceeded"""
        with self.lock:
            now = time.time()

            # Remove calls older than period
            while self.calls and self.calls[0] < now - self.period:
                self.calls.popleft()

            # If at limit, wait
            if len(self.calls) >= self.max_calls:
                sleep_time = self.calls[0] + self.period - now
                if sleep_time > 0:
                    print(f"⏳ Rate limit: waiting {sleep_time:.1f}s")
                    time.sleep(sleep_time)
                    self.calls.popleft()

            # Record this call
            self.calls.append(time.time())
