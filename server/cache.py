import time
from typing import Any


class TTLCache:
    def __init__(self, default_ttl: int = 300, max_size: int = 512):
        self._store: dict[str, tuple[float, Any]] = {}
        self._default_ttl = default_ttl
        self._max_size = max_size

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires, value = entry
        if time.monotonic() > expires:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        if key not in self._store and len(self._store) >= self._max_size:
            self._evict()
        expires = time.monotonic() + (ttl or self._default_ttl)
        self._store[key] = (expires, value)

    def _evict(self) -> None:
        now = time.monotonic()
        expired = [k for k, (exp, _) in self._store.items() if now > exp]
        for k in expired:
            del self._store[k]
        overflow = len(self._store) - self._max_size + 1
        if overflow > 0:
            by_expiry = sorted(self._store, key=lambda k: self._store[k][0])
            for k in by_expiry[:overflow]:
                del self._store[k]

    def clear(self) -> None:
        self._store.clear()
