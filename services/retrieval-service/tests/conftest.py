import os

os.environ["RETRIEVE_DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["RETRIEVE_GROQ_API_KEY"] = "test-key"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from src import llm, main, retriever  # noqa: E402
from src.db import engine  # noqa: E402
from src.models import ChatHistory  # noqa: E402


@pytest.fixture
def client(monkeypatch) -> TestClient:
    # chat_history is plain SQL (sqlite-friendly); document_chunks (pgvector) is never
    # created here because retrieval is mocked.
    ChatHistory.__table__.create(bind=engine, checkfirst=True)

    monkeypatch.setattr(main, "embed", lambda texts: [[0.0] * 1024 for _ in texts])
    monkeypatch.setattr(retriever, "retrieve", lambda *a, **k: ["context one", "context two"])
    monkeypatch.setattr(llm, "stream_answer", lambda q, c: iter(["Hello", " world"]))

    with TestClient(main.app) as c:
        yield c

    ChatHistory.__table__.drop(bind=engine)
