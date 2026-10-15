from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from server.gp_client import cache
from server.main import app
from server.rate_limit import RateLimitMiddleware


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    """Réinitialise le cache amont et le rate limiter entre chaque test."""
    cache.clear()
    yield
    cache.clear()
    layer = app.middleware_stack
    while layer is not None:
        if isinstance(layer, RateLimitMiddleware):
            layer.clear()
            break
        layer = getattr(layer, "app", None)
