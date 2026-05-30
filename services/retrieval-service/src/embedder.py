from functools import lru_cache

from src.config import settings


@lru_cache(maxsize=1)
def _model():
    # Lazy import: torch/sentence-transformers are the `ml` extra, absent in local dev.
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.model_name)


def embed(texts: list[str]) -> list[list[float]]:
    """Same embedder as embedding-service so query and stored vectors share a space."""
    vectors = _model().encode(texts, normalize_embeddings=True)
    return [v.tolist() for v in vectors]
