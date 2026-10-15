import time
from typing import Any


class TTLCache:
    def __init__(self, default_ttl: int = 300):
        self._store: dict[str, tuple[float, Any]] = {}
        self._default_ttl = default_ttl

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
        expires = time.monotonic() + (ttl or self._default_ttl)
        self._store[key] = (expires, value)

    def clear(self) -> None:
        self._store.clear()