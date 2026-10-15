from __future__ import annotations

from unittest.mock import patch

XFF_A = {"X-Forwarded-For": "1.2.3.4"}
XFF_B = {"X-Forwarded-For": "5.6.7.8"}


def test_rate_limit_triggers_after_30_requests(client):
    with patch("server.gp_client._fetch", return_value=[]):
        for i in range(30):
            resp = client.get("/api/v1/calendar?year=2026")
            assert resp.status_code == 200, f"requête {i + 1} bloquée"
        resp = client.get("/api/v1/calendar?year=2026")
        assert resp.status_code == 429


def test_rate_limit_isolated_per_ip_via_xff(client):
    """Chaque IP (via X-Forwarded-For) a son propre quota."""
    with patch("server.gp_client._fetch", return_value=[]):
        for _ in range(30):
            client.get("/api/v1/calendar?year=2026", headers=XFF_A)
        blocked = client.get("/api/v1/calendar?year=2026", headers=XFF_A)
        other_ip = client.get("/api/v1/calendar?year=2026", headers=XFF_B)
    assert blocked.status_code == 429
    assert other_ip.status_code == 200


def test_health_exempt_from_rate_limit(client):
    with patch("server.gp_client._fetch", return_value=[]):
        for _ in range(35):
            client.get("/api/v1/calendar?year=2026")
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
