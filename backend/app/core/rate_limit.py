"""In-process sliding-window rate limiter.

Adequate for a single-instance deployment. Behind several workers or replicas, replace it
with a shared store (for example Redis) or a gateway-level limit.
"""

from __future__ import annotations

import math
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable


class SlidingWindowLimiter:
    def __init__(
        self,
        limit: int,
        window_seconds: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._limit = limit
        self._window = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> int:
        """Record a hit. Returns 0 when allowed, else the seconds until a slot frees up."""
        if self._limit <= 0:
            return 0
        now = self._clock()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] >= self._window:
                hits.popleft()
            if len(hits) >= self._limit:
                return max(1, math.ceil(self._window - (now - hits[0])))
            hits.append(now)
            return 0
