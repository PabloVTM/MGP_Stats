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
MAX_RETRIES = 3

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
_inflight: dict[str, asyncio.Task] = {}
_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    """Client HTTP partagé (connection pooling), créé à la première utilisation."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=TIMEOUT, headers=_HEADERS)
    return _client


async def close_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def _now() -> datetime:
    return datetime.now(UTC)


def _current_year() -> int:
    return _now().year


def _weekend_ttl() -> int:
    return 3600 if _now().weekday() >= 4 else 86400


async def _fetch(path: str) -> Any:
    url = f"{BASE_URL}/{path}"
    cached = cache.get(url)
    if cached is not None:
        return cached
    # Déduplication : les requêtes concurrentes partagent le même fetch.
    # La tâche est retirée du dict dès sa complétion (pas de fuite mémoire).
    task = _inflight.get(url)
    if task is None:
        task = asyncio.create_task(_fetch_upstream(url))
        _inflight[url] = task
        task.add_done_callback(lambda _t, u=url: _inflight.pop(u, None))
    return await task


async def _fetch_upstream(url: str) -> Any:
    client = _get_client()
    last_exc: Exception = httpx.HTTPError(f"Échec après {MAX_RETRIES} tentatives: {url}")
    for attempt in range(MAX_RETRIES):
        try:
            resp = await client.get(url)
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            last_exc = e
        else:
            if resp.status_code != 429 and resp.status_code < 500:
                resp.raise_for_status()
                data = resp.json()
                cache.set(url, data, ttl=_weekend_ttl())
                return data
            last_exc = httpx.HTTPStatusError(
                f"{resp.status_code} (after {MAX_RETRIES} retries)",
                request=resp.request,
                response=resp,
            )
        wait = 4 ** attempt
        logger.warning("Retry %d/%d sur %s, attente %ds (%s)", attempt + 1, MAX_RETRIES, url, wait, last_exc)
        await asyncio.sleep(wait)
    logger.error("Abandon après %d tentatives pour %s", MAX_RETRIES, url)
    raise last_exc


def _to_int(val: str | float) -> int:
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
            raw = _val(val).strip()
            if raw:
                return raw
    return ""


def _short_name(full: str) -> str:
    parts = full.rsplit(" ", 1)
    if len(parts) > 1 and parts[0]:
        return f"{parts[0][0]}. {parts[-1]}"
    return full


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
    explicit_year = year is not None
    cal = await get_calendar(year)
    today = _now().strftime("%Y-%m-%d")
    for r in cal:
        if r["date"] >= today:
            return r
    if explicit_year:
        return cal[-1] if cal else None
    # Hors saison : bascule sur le premier GP de l'année suivante
    next_year_cal = await get_calendar(_current_year() + 1)
    if next_year_cal:
        return next_year_cal[0]
    return cal[-1] if cal else None


# ── Rider Standings ───────────────────────────────────────────────────────────


async def get_rider_standings(
    year: int | None = None
) -> list[dict[str, Any]]:
    year = year or _current_year()
    season_uuid = await _season_uuid(year)
    if not season_uuid:
        return []
    cat_uuid = await _category_uuid(season_uuid, "MotoGP")
    if not cat_uuid:
        return []

    data = await _fetch(
        f"results/standings?seasonUuid={season_uuid}&categoryUuid={cat_uuid}"
    )
    classification = data.get("classification") or []

    result = []
    for c in classification:
        rider = c.get("rider", {}) or {}
        full = rider.get("full_name", "")
        result.append(
            {
                "pos": _to_int(c.get("position", 0)),
                "name": _short_name(full),
                "pts": _to_int(c.get("points", 0)),
            }
        )
    return result
