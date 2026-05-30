from collections.abc import Callable

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from src.config import settings
from src.models import DocumentChunk

EmbedFn = Callable[[list[str]], list[list[float]]]


def rrf_fuse(ranked_lists: list[list[str]], k: int | None = None) -> list[str]:
    """Reciprocal Rank Fusion: combine ranked id lists into one ranking.

    score(id) = sum over lists of 1 / (k + rank). Pure function — unit tested.
    """
    k = k or settings.rrf_k
    scores: dict[str, float] = {}
    for ids in ranked_lists:
        for rank, doc_id in enumerate(ids):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores, key=lambda i: scores[i], reverse=True)


def _vector_search(session: Session, query_vector: list[float], limit: int) -> list[str]:
    stmt = (
        select(DocumentChunk.id)
        .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
        .limit(limit)
    )
    return list(session.scalars(stmt))


def _keyword_search(session: Session, query: str, limit: int) -> list[str]:
    stmt = text(
        """
        SELECT id FROM document_chunks
        WHERE to_tsvector('english', chunk_text) @@ plainto_tsquery('english', :q)
        ORDER BY ts_rank(to_tsvector('english', chunk_text), plainto_tsquery('english', :q)) DESC
        LIMIT :limit
        """
    )
    return [str(row[0]) for row in session.execute(stmt, {"q": query, "limit": limit})]


def retrieve(
    session: Session, query: str, embed_fn: EmbedFn, top_k: int | None = None
) -> list[str]:
    """Hybrid retrieval: vector + keyword, fused by RRF. Returns chunk texts, best first."""
    top_k = top_k or settings.top_k
    pool = top_k * 2

    query_vector = embed_fn([query])[0]
    vector_ids = _vector_search(session, query_vector, pool)
    keyword_ids = _keyword_search(session, query, pool)

    fused = rrf_fuse([vector_ids, keyword_ids])[:top_k]
    if not fused:
        return []

    rows = session.scalars(select(DocumentChunk).where(DocumentChunk.id.in_(fused)))
    text_by_id = {c.id: c.chunk_text for c in rows}
    return [text_by_id[i] for i in fused if i in text_by_id]
