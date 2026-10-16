from __future__ import annotations
import time
from collections import defaultdict, deque
from threading import Lock
from typing import Deque, Dict, Tuple

_LOCK = Lock()
_BUCKETS: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)


def allow(key: str, subject: str, max_events: int, window_seconds: float) -> bool:
    now = time.monotonic()
    cutoff = now - window_seconds
    with _LOCK:
        bucket = _BUCKETS[(key, subject)]
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= max_events:
            return False
        bucket.append(now)
        return True
