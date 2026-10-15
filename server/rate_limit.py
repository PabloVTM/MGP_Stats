from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

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

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path == "/api/v1/health":
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window = self.window_seconds

        timestamps = self._store[ip]
        cutoff = now - window
        timestamps[:] = [t for t in timestamps if t > cutoff]

        if len(timestamps) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"err": "rate_limit", "msg": "Trop de requêtes, réessaie dans quelques secondes"},
            )

        timestamps.append(now)
        return await call_next(request)