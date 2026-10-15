from __future__ import annotations

from unittest.mock import patch

import httpx

# ── Health ────────────────────────────────────────────────────────────────────


def test_health(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert "ts" in body


# ── Calendar ──────────────────────────────────────────────────────────────────


def test_calendar_filters_sorts_strips(client):
    events = [
        {"kind": "GP", "sequence": 2, "name": "Spanish Grand Prix ", "date_start": "2026-04-19T10:00:00"},
        {"kind": "TEST", "sequence": 1, "name": "Pre-season test", "date_start": "2026-02-01T00:00:00"},
        {"kind": "GP", "sequence": 1, "name": "Qatar Grand Prix", "date_start": "2026-03-08T10:00:00"},
    ]
    with patch("server.gp_client._fetch", return_value=events):
        resp = client.get("/api/v1/calendar?year=2026")
    assert resp.status_code == 200
    cal = resp.json()["cal"]
    assert [r["rnd"] for r in cal] == [1, 2]
    assert cal[0] == {"rnd": 1, "name": "Qatar Grand Prix", "date": "2026-03-08"}
    assert cal[1]["name"] == "Spanish Grand Prix"  # strippé


def test_calendar_invalid_year(client):
    resp = client.get("/api/v1/calendar?year=1000")
    assert resp.status_code == 422
    resp = client.get("/api/v1/calendar?year=3000")
    assert resp.status_code == 422


# ── Next ──────────────────────────────────────────────────────────────────────


def test_next_returns_future_event(client):
    events = [
        {"kind": "GP", "sequence": 1, "name": "Past GP", "date_start": "2020-01-01T00:00:00"},
        {"kind": "GP", "sequence": 2, "name": "Future GP", "date_start": "2999-01-01T00:00:00"},
    ]
    with patch("server.gp_client._fetch", return_value=events):
        resp = client.get("/api/v1/next?year=2026")
    assert resp.status_code == 200
    assert resp.json()["next"]["name"] == "Future GP"


def test_next_explicit_year_all_past_returns_last(client):
    events = [
        {"kind": "GP", "sequence": 1, "name": "GP One", "date_start": "2020-01-01T00:00:00"},
        {"kind": "GP", "sequence": 2, "name": "GP Two", "date_start": "2020-06-01T00:00:00"},
    ]
    with patch("server.gp_client._fetch", return_value=events):
        resp = client.get("/api/v1/next?year=2020")
    assert resp.status_code == 200
    assert resp.json()["next"]["name"] == "GP Two"


def test_next_offseason_switches_to_next_year(client):
    past = [{"kind": "GP", "sequence": 1, "name": "Last GP", "date_start": "2020-01-01T00:00:00"}]
    future = [{"kind": "GP", "sequence": 1, "name": "First GP Next Year", "date_start": "2027-03-01T00:00:00"}]
    calls = []

    def fake_fetch(path):
        calls.append(path)
        return past if len(calls) == 1 else future

    with patch("server.gp_client._fetch", side_effect=fake_fetch):
        resp = client.get("/api/v1/next")  # sans year → bascule sur N+1
    assert resp.status_code == 200
    assert resp.json()["next"]["name"] == "First GP Next Year"
    assert len(calls) == 2


# ── Standings ─────────────────────────────────────────────────────────────────


def _fake_standings_fetch(path: str):
    if path == "results/seasons":
        return [{"year": 2026, "id": "s1"}]
    if path.startswith("results/categories"):
        return [{"name": "MotoGP™", "id": "c1"}]
    if path.startswith("results/standings"):
        return {
            "classification": [
                {"position": 1, "points": 355, "rider": {"full_name": "Jorge Martin"}},
                {"position": 2, "points": 340, "rider": {"full_name": "Marc Marquez"}},
            ]
        }
    raise AssertionError(f"URL inattendue: {path}")


def test_standings(client):
    with patch("server.gp_client._fetch", side_effect=_fake_standings_fetch):
        resp = client.get("/api/v1/standings?year=2026")
    assert resp.status_code == 200
    assert resp.json()["drv"] == [
        {"pos": 1, "name": "J. Martin", "pts": 355},
        {"pos": 2, "name": "M. Marquez", "pts": 340},
    ]


# ── Erreurs ───────────────────────────────────────────────────────────────────


def test_upstream_error_returns_generic_503(client):
    with patch("server.gp_client._fetch", side_effect=httpx.HTTPError("boom internal detail")):
        resp = client.get("/api/v1/calendar?year=2026")
    assert resp.status_code == 503
    assert resp.json()["detail"] == "API MotoGP indisponible"
    assert "boom" not in resp.text  # pas de fuite du détail interne


def test_404(client):
    resp = client.get("/api/v1/nonexistent")
    assert resp.status_code == 404
