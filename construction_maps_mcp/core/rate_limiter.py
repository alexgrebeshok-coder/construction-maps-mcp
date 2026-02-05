"""Rate limiting using sliding window algorithm."""

import asyncio
import time
from collections import deque


class RateLimiter:
    """
    Sliding window rate limiter.

    Ensures that no more than N requests are made in a given time window.
    """

    def __init__(self, requests_per_minute: int = 15):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests allowed per minute
        """
        self.rpm = requests_per_minute
        self.window_seconds = 60
        self.requests: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """
        Acquire permission to make a request.

        This method will block (sleep) if the rate limit would be exceeded.
        """
        async with self._lock:
            now = time.time()

            # Remove requests older than window
            while self.requests and self.requests[0] < now - self.window_seconds:
                self.requests.popleft()

            # If at limit, wait until oldest request expires
            if len(self.requests) >= self.rpm:
                sleep_time = self.window_seconds - (now - self.requests[0]) + 0.1
                await asyncio.sleep(sleep_time)

                # Clean up again after sleeping
                now = time.time()
                while self.requests and self.requests[0] < now - self.window_seconds:
                    self.requests.popleft()

            # Record this request
            self.requests.append(now)

    def get_remaining(self) -> int:
        """Get number of remaining requests in current window."""
        now = time.time()
        # Clean expired requests
        while self.requests and self.requests[0] < now - self.window_seconds:
            self.requests.popleft()
        return max(0, self.rpm - len(self.requests))

    def reset(self) -> None:
        """Reset rate limiter (clear all tracked requests)."""
        self.requests.clear()
