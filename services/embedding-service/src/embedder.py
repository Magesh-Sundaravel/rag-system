from functools import lru_cache

from src.config import settings


@lru_cache(maxsize=1)
def _model():
    # Imported lazily: torch/sentence-transformers are the `ml` extra, absent in local dev.
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.model_name)


def embed(texts: list[str]) -> list[list[float]]:
    """Embed texts with bge-large (normalized for cosine). Returns 1024-dim vectors."""
    vectors = _model().encode(texts, normalize_embeddings=True)
    return [v.tolist() for v in vectors]
