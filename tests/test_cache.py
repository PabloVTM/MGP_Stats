from __future__ import annotations

import asyncio
import time
from unittest.mock import patch

import pytest

from server import gp_client
from server.cache import TTLCache


def test_get_returns_value_within_ttl():
    c = TTLCache(default_ttl=10)
    c.set("k", "v")
    assert c.get("k") == "v"


def test_ttl_expiry():
    c = TTLCache(default_ttl=10)
    c.set("k", "v")
    with patch("server.cache.time.monotonic", return_value=time.monotonic() + 11):
        assert c.get("k") is None


def test_eviction_removes_oldest_when_full():
    c = TTLCache(default_ttl=60, max_size=2)
    c.set("a", 1)
    c.set("b", 2)
    c.set("c", 3)  # dépasse max_size → éviction
    assert c.get("a") is None
    assert c.get("b") == 2
    assert c.get("c") == 3


def test_eviction_prefers_expired_entries():
    c = TTLCache(default_ttl=60, max_size=2)
    c.set("a", 1, ttl=1)
    c.set("b", 2)
    with patch("server.cache.time.monotonic", return_value=time.monotonic() + 2):
        c.set("c", 3)  # "a" expiré → évincé en priorité, "b" conservé
        assert c.get("b") == 2
        assert c.get("c") == 3


@pytest.mark.asyncio
async def test_fetch_dedupes_concurrent_calls():
    """2 appels concurrents sur la même URL → 1 seul hit amont."""
    with patch.object(gp_client, "_fetch_upstream", return_value={"ok": True}) as upstream:
        r1, r2 = await asyncio.gather(
            gp_client._fetch("events?seasonYear=2026"),
            gp_client._fetch("events?seasonYear=2026"),
        )
    assert r1 == r2 == {"ok": True}
    assert upstream.call_count == 1


@pytest.mark.asyncio
async def test_fetch_serves_from_cache():
    """Une URL déjà en cache ne déclenche aucun appel amont."""
    gp_client.cache.set(f"{gp_client.BASE_URL}/results/seasons", [1, 2], ttl=60)
    with patch.object(gp_client, "_fetch_upstream") as upstream:
        result = await gp_client._fetch("results/seasons")
    assert result == [1, 2]
    assert upstream.call_count == 0
