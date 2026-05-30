import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from src.chunkers import CHUNKERS
from src.db import Base, engine, get_db
from src.detector import detect
from src.jobs import IngestJob
from src.pipelines import ocr, text
from src.queue import enqueue_chunks
from src.storage import upload_raw

logger = logging.getLogger("ingestion")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="ingestion-service", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest(file: UploadFile = File(...), db: Session = Depends(get_db)) -> dict:
    data = await file.read()
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty file")

    filename = file.filename or "upload"
    det = detect(filename, file.content_type)
    document_id = str(uuid4())

    # Raw file goes to S3; service stays stateless.
    upload_raw(f"raw/{document_id}/{filename}", data, det.mime)

    if det.pipeline == "ocr":
        extracted = ocr.extract(data)
    else:
        extracted = text.extract(data, det.mime, filename)
    chunks = CHUNKERS[det.strategy](extracted)

    metadata = {"source": filename, "mime": det.mime}
    enqueue_chunks(document_id, chunks, metadata)

    # Observability: every chunking decision is logged (no file contents / secrets).
    logger.info(
        "chunked document",
        extra={
            "document_id": document_id,
            "strategy_used": det.strategy,
            "chunk_count": len(chunks),
        },
    )

    job = IngestJob(
        document_id=document_id,
        status="queued",
        detected_type=det.mime,
        pipeline=det.pipeline,
        strategy=det.strategy,
        chunk_count=len(chunks),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    return {
        "job_id": job.id,
        "document_id": document_id,
        "detected_type": det.mime,
        "pipeline": det.pipeline,
        "strategy_used": det.strategy,
        "chunk_count": len(chunks),
    }


@app.get("/status/{job_id}")
def job_status(job_id: str, db: Session = Depends(get_db)) -> dict:
    job = db.get(IngestJob, job_id)
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    return {
        "job_id": job.id,
        "document_id": job.document_id,
        "status": job.status,
        "detected_type": job.detected_type,
        "pipeline": job.pipeline,
        "strategy_used": job.strategy,
        "chunk_count": job.chunk_count,
    }
