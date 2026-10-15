from __future__ import annotations

import asyncio
import logging
import os
from datetime import UTC, datetime
from typing import Any

import httpx

from server.cache import TTLCache

logger = logging.getLogger(__name__)

BASE_URL = os.getenv("MGP_API_URL") or "https://api.pulselive.motogp.com/motogp/v1"
API_KEY = os.getenv("MGP_API_KEY") or ""
TIMEOUT = httpx.Timeout(20.0)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.motogp.com",
    "Referer": "https://www.motogp.com/",
}
if API_KEY:
    _HEADERS["X-API-Key"] = API_KEY
    _HEADERS["Authorization"] = f"Bearer {API_KEY}"

cache = TTLCache()


def _now() -> datetime:
    return datetime.now(UTC)


def _current_year() -> int:
    return _now().year


def _weekend_ttl() -> int:
    return 3600 if _now().weekday() >= 4 else 86400


async def _fetch(path: str) -> Any:
    url = f"{BASE_URL}/{path}"
    cached = cache.get(url)
    if cached:
        return cached
    for attempt in range(3):
        async with httpx.AsyncClient(timeout=TIMEOUT, headers=_HEADERS) as client:
            resp = await client.get(url)
            if resp.status_code == 429:
                wait = 4 ** attempt
                logger.warning("429 sur %s, attente %ds", url, wait)
                await asyncio.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            cache.set(url, data, ttl=_weekend_ttl())
            return data
    logger.error("Abandon après 3 tentatives pour %s", url)
    raise httpx.HTTPStatusError(
        "429 Too Many Requests (after 3 retries)",
        request=resp.request,
        response=resp,
    )


def _to_int(val: str | int | float) -> int:
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0


def _val(obj: Any) -> str:
    if isinstance(obj, dict):
        return obj.get("value", "")
    return str(obj) if obj else ""


def _event_name(e: dict[str, Any]) -> str:
    for field in ("name", "full_name", "event_name", "description"):
        val = e.get(field)
        if val:
            raw = _val(val)
            if raw:
                return raw
    return ""


# ── Season helpers ────────────────────────────────────────────────────────────


async def _season_uuid(year: int | None = None) -> str:
    year = year or _current_year()
    seasons = await _fetch("results/seasons")
    for s in seasons:
        if s.get("year") == year:
            return s["id"]
    return ""


async def _category_uuid(season_uuid: str, category: str = "MotoGP") -> str:
    cats = await _fetch(f"results/categories?seasonUuid={season_uuid}")
    for c in cats:
        cname = c.get("name", "").replace("\u2122", "")
        if cname.strip() == category:
            return c["id"]
    return ""


# ── Calendar ──────────────────────────────────────────────────────────────────


async def get_calendar(year: int | None = None) -> list[dict[str, Any]]:
    year = year or _current_year()
    events = await _fetch(f"events?seasonYear={year}")

    result = []
    for e in events:
        if e.get("kind") != "GP":
            continue
        result.append(
            {
                "rnd": _to_int(e.get("sequence", 0)),
                "name": _event_name(e),
                "date": (e.get("date_start") or "")[:10],
            }
        )
    return sorted(result, key=lambda x: x["rnd"])


# ── Next Event ────────────────────────────────────────────────────────────────


async def get_next_event(year: int | None = None) -> dict[str, Any] | None:
    year = year or _current_year()
    cal = await get_calendar(year)
    today = _now().strftime("%Y-%m-%d")
    for r in cal:
        if r["date"] >= today:
            return r
    return cal[-1] if cal else None


# ── Rider Standings ───────────────────────────────────────────────────────────


async def get_rider_standings(
    year: int | None = None, category: str = "MotoGP"
) -> list[dict[str, Any]]:
    year = year or _current_year()
    season_uuid = await _season_uuid(year)
    if not season_uuid:
        return []
    cat_uuid = await _category_uuid(season_uuid, category)
    if not cat_uuid:
        return []

    data = await _fetch(
        f"results/standings?seasonUuid={season_uuid}&categoryUuid={cat_uuid}"
    )
    classification = data.get("classification") or []

    result = []
    for c in classification:
        rider = c.get("rider", {}) or {}
        team = c.get("team", {}) or {}
        full = rider.get("full_name", "")
        result.append(
            {
                "pos": _to_int(c.get("position", 0)),
                "name": _short_name(full),
                "team": team.get("name", ""),
                "pts": _to_int(c.get("points", 0)),
            }
        )
    return result