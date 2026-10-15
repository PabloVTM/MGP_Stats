from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: FastAPI,
        max_requests: int = 60,
        window_seconds: int = 60,
    ) -> None:
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._store: dict[str, list[float]] = defaultdict(list)
        self._last_sweep = time.monotonic()

    def _sweep(self, now: float) -> None:
        """Purge les IPs inactives pour éviter une croissance mémoire illimitée."""
        if now - self._last_sweep < self.window_seconds:
            return
        self._last_sweep = now
        cutoff = now - self.window_seconds
        inactive = [ip for ip, ts in self._store.items() if not ts or ts[-1] <= cutoff]
        for ip in inactive:
            del self._store[ip]

    def clear(self) -> None:
        self._store.clear()

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path == "/api/v1/health":
            return await call_next(request)

        # X-Forwarded-For posé par le reverse proxy de confiance (Traefik/WAF).
        # Ne pas exposer le conteneur directement : l'en-tête serait spoofable.
        xff = request.headers.get("x-forwarded-for")
        if xff:
            ip = xff.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        self._sweep(now)

        timestamps = self._store[ip]
        cutoff = now - self.window_seconds
        timestamps[:] = [t for t in timestamps if t > cutoff]

        if len(timestamps) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"err": "rate_limit", "msg": "Trop de requêtes, réessaie dans quelques secondes"},
            )

        timestamps.append(now)
        return await call_next(request)
