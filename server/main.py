from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query

from server.gp_client import (
    close_client,
    get_calendar,
    get_next_event,
    get_rider_standings,
)
from server.rate_limit import RateLimitMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

ENABLE_DOCS = os.getenv("MGP_ENABLE_DOCS", "").lower() in ("1", "true", "yes")

YearParam = Annotated[int | None, Query(ge=1949, le=2100)]

UPSTREAM_ERROR = "API MotoGP indisponible"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await close_client()


app = FastAPI(
    title="MGP Stats API",
    description="Données MotoGP simplifiées pour ESP32 — une requête = une donnée",
    version="1.1.0",
    docs_url="/docs" if ENABLE_DOCS else None,
    redoc_url=None,
    openapi_url="/openapi.json" if ENABLE_DOCS else None,
    lifespan=lifespan,
)
app.add_middleware(RateLimitMiddleware, max_requests=30, window_seconds=60)


@app.get("/api/v1/calendar")
async def calendar(year: YearParam = None):
    """Calendrier complet de la saison (GP, dates)."""
    try:
        return {"cal": await get_calendar(year)}
    except Exception:
        logger.exception("Erreur lors de la récupération du calendrier")
        raise HTTPException(503, UPSTREAM_ERROR) from None


@app.get("/api/v1/next")
async def next_event(year: YearParam = None):
    """Prochain GP au calendrier."""
    try:
        return {"next": await get_next_event(year)}
    except Exception:
        logger.exception("Erreur lors de la récupération du prochain GP")
        raise HTTPException(503, UPSTREAM_ERROR) from None


@app.get("/api/v1/standings")
async def rider_standings(year: YearParam = None):
    """Classement pilotes MotoGP (position, nom, points)."""
    try:
        data = await get_rider_standings(year)
        return {"drv": data}
    except Exception:
        logger.exception("Erreur lors de la récupération du classement")
        raise HTTPException(503, UPSTREAM_ERROR) from None


@app.get("/api/v1/health")
async def health():
    return {"ok": True, "ts": datetime.now(UTC).isoformat()}
