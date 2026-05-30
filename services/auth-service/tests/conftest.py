import os

os.environ["AUTH_DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["AUTH_JWT_SECRET"] = "test-secret"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from src.main import app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as c:
        yield c
