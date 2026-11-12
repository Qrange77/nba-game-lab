"""One research run's bounded, deduplicated API access, shared across contexts."""
import json
import time
from threading import Lock, BoundedSemaphore
from backend.data.nba import NBAData, DataUnavailable


class ResearchData(NBAData):
    def __init__(self, deadline, cache_path=None, max_requests=120):
        super().__init__(cache_path=cache_path)
        self.deadline = deadline
        self.max_requests = max_requests
        self.requests = 0
        self.guard = Lock()
        self.keys = {}
        self.slots = BoundedSemaphore(4)

    @property
    def remaining_seconds(self):
        return max(0, self.deadline - time.monotonic())

    def fetch(self, kind, **params):
        key = json.dumps([kind, params], sort_keys=True)
        with self.guard:
            lock = self.keys.setdefault(key, Lock())
        if not lock.acquire(timeout=self.remaining_seconds):
            raise DataUnavailable('Research time limit reached while waiting for data.')
        try:
            return super().fetch(kind, **params)
        finally:
            lock.release()

    def _live(self, kind, params, timeout):
        if not self.slots.acquire(timeout=self.remaining_seconds):
            raise DataUnavailable('Research time limit reached while waiting for an API slot.')
        try:
            with self.guard:
                if self.requests >= self.max_requests or self.remaining_seconds <= 0:
                    raise DataUnavailable('The shared research API budget was reached; coverage is partial.')
                self.requests += 1
            return super()._live(kind, params, min(timeout, self.remaining_seconds, 12))
        finally:
            self.slots.release()
