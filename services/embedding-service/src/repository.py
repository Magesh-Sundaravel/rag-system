import hashlib
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import DocumentChunk


def compute_hash(document_id: str, chunk_index: int, chunk_text: str) -> str:
    """Stable hash for idempotency. Same (doc, index, text) -> same hash."""
    digest = hashlib.sha256()
    digest.update(f"{document_id}:{chunk_index}:".encode())
    digest.update(chunk_text.encode())
    return digest.hexdigest()


class ChunkRepository:
    def __init__(self, session: Session):
        self.session = session

    def exists(self, chunk_hash: str) -> bool:
        stmt = select(DocumentChunk.id).where(DocumentChunk.chunk_hash == chunk_hash)
        return self.session.scalar(stmt) is not None

    def insert(
        self,
        *,
        document_id: UUID,
        chunk_text: str,
        chunk_hash: str,
        embedding: list[float],
        metadata: dict,
    ) -> None:
        self.session.add(
            DocumentChunk(
                document_id=document_id,
                chunk_text=chunk_text,
                chunk_hash=chunk_hash,
                embedding=embedding,
                chunk_metadata=metadata,
            )
        )
        self.session.commit()
