from src.config import settings
from src.consumer import handle_message
from tests.conftest import FakeRepo, fake_embed


def _message():
    return {
        "document_id": "doc1",
        "chunk_index": 0,
        "chunk_text": "the quick brown fox",
        "metadata": {"source": "a.txt"},
    }


def test_stores_chunk_with_1024_dim_vector():
    repo = FakeRepo()
    result = handle_message(_message(), repo, fake_embed)
    assert result == "stored"
    assert len(repo.stored) == 1
    stored = next(iter(repo.stored.values()))
    assert len(stored["embedding"]) == settings.embed_dim == 1024


def test_idempotent_skips_re_embedding():
    repo = FakeRepo()
    calls: list[list[str]] = []

    def counting_embed(texts):
        calls.append(texts)
        return fake_embed(texts)

    assert handle_message(_message(), repo, counting_embed) == "stored"
    assert handle_message(_message(), repo, counting_embed) == "skipped"
    assert len(repo.stored) == 1
    assert len(calls) == 1  # second message never re-embedded
