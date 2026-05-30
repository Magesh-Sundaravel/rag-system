import os

os.environ["INGEST_DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from src import main  # noqa: E402


@pytest.fixture
def client(monkeypatch) -> TestClient:
    # Stub AWS so endpoint tests need no S3/SQS.
    monkeypatch.setattr(main, "upload_raw", lambda *a, **k: "s3://test/key")
    monkeypatch.setattr(main, "enqueue_chunks", lambda *a, **k: None)
    with TestClient(main.app) as c:
        yield c
