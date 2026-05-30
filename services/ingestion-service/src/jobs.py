from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db import Base


class IngestJob(Base):
    """Tracks a single ingest request. Stateless: lives in Postgres, not memory."""

    __tablename__ = "ingest_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    document_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # queued | failed
    detected_type: Mapped[str] = mapped_column(String(128), nullable=False)
    pipeline: Mapped[str] = mapped_column(String(16), nullable=False)  # ocr | text
    strategy: Mapped[str] = mapped_column(String(16), nullable=False)  # fixed|recursive|sentence
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
