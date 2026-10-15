from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException, Query

from server.gp_client import (
    get_calendar,
    get_event_sessions,
    get_next_event,
    get_rider_standings,
)
from server.rate_limit import RateLimitMiddleware

logger = logging.getLogger(__name__)

app = FastAPI(
    title="MGP Stats API",
    description="Données MotoGP simplifiées pour ESP32 — une requête = une donnée",
    version="1.0.0",
)
app.add_middleware(RateLimitMiddleware, max_requests=30, window_seconds=60)


@app.get("/api/v1/calendar")
async def calendar(year: int | None = None):
    """Calendrier complet de la saison (GP, dates)."""
    try:
        return {"cal": await get_calendar(year)}
    except Exception as e:
        raise HTTPException(503, f"Erreur API MotoGP: {e}")


@app.get("/api/v1/next")
async def next_event(year: int | None = None):
    """Prochain GP au calendrier."""
    try:
        return {"next": await get_next_event(year)}
    except Exception as e:
        raise HTTPException(503, f"Erreur API MotoGP: {e}")


@app.get("/api/v1/sessions")
async def sessions(
    round: int = Query(..., description="Numéro du round"),
    year: int | None = None,
    category: str = "MotoGP",
):
    """Horaires des séances pour un GP donné (FP1-4, Q1/Q2, RAC, SPR...)."""
    try:
        data = await get_event_sessions(round, year, category)
        return {"sessions": data}
    except Exception as e:
        raise HTTPException(503, f"Erreur API MotoGP: {e}")


@app.get("/api/v1/standings")
async def rider_standings(
    year: int | None = None,
    category: str = "MotoGP",
):
    """Classement pilotes d'une catégorie (MotoGP, Moto2, Moto3, MotoE)."""
    try:
        data = await get_rider_standings(year, category)
        return {"drv": data}
    except Exception as e:
        raise HTTPException(503, f"Erreur API MotoGP: {e}")


@app.get("/api/v1/health")
async def health():
    return {"ok": True, "ts": datetime.now(UTC).isoformat()}