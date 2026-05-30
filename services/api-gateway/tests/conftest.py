import os
from datetime import UTC, datetime, timedelta

os.environ["GATEWAY_JWT_SECRET"] = "test-secret"

import httpx  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from jose import jwt  # noqa: E402

from src import main, proxy  # noqa: E402


async def _sse_body():
    # Async stream so the gateway's streaming proxy (aiter_raw) works under MockTransport.
    yield b'data: {"delta": "hi"}\n\n'


def _downstream(request: httpx.Request) -> httpx.Response:
    """Fake the three backend services."""
    path = request.url.path
    if path == "/login":
        return httpx.Response(200, json={"access_token": "a", "refresh_token": "r"})
    if path == "/ingest":
        return httpx.Response(202, json={"job_id": "j1", "strategy_used": "sentence"})
    if path == "/query":
        return httpx.Response(
            200,
            content=_sse_body(),
            headers={"content-type": "text/event-stream"},
        )
    return httpx.Response(404, json={"detail": "not found"})


@pytest.fixture
def client() -> TestClient:
    proxy.client = httpx.AsyncClient(transport=httpx.MockTransport(_downstream))
    with TestClient(main.app) as c:
        yield c
    proxy.client = None


def make_token(token_type: str = "access") -> str:
    payload = {
        "sub": "u1",
        "type": token_type,
        "exp": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp()),
    }
    return jwt.encode(payload, "test-secret", algorithm="HS256")
