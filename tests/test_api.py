from __future__ import annotations
from unittest.mock import patch

from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert "ts" in body


def test_sessions_missing_round():
    resp = client.get("/api/v1/sessions")
    assert resp.status_code == 422


def test_race_results_missing_round():
    resp = client.get("/api/v1/results/race")
    assert resp.status_code == 404


def test_404():
    resp = client.get("/api/v1/nonexistent")
    assert resp.status_code == 404