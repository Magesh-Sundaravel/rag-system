from src.config import settings


class FakeRepo:
    """In-memory stand-in for ChunkRepository (no Postgres/pgvector needed)."""

    def __init__(self):
        self.stored: dict[str, dict] = {}

    def exists(self, chunk_hash: str) -> bool:
        return chunk_hash in self.stored

    def insert(self, *, chunk_hash: str, embedding: list[float], **kwargs) -> None:
        self.stored[chunk_hash] = {"embedding": embedding, **kwargs}


def fake_embed(texts: list[str]) -> list[list[float]]:
    return [[0.1] * settings.embed_dim for _ in texts]
