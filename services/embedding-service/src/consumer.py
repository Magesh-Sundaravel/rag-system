import json
import logging
from collections.abc import Callable
from uuid import UUID

import boto3

from src.config import settings
from src.db import SessionLocal
from src.embedder import embed
from src.repository import ChunkRepository, compute_hash

logger = logging.getLogger("embedding")

# Embedder signature: list[str] -> list[list[float]]. Injectable for testing.
EmbedFn = Callable[[list[str]], list[list[float]]]


def handle_message(body: dict, repo: ChunkRepository, embed_fn: EmbedFn) -> str:
    """Embed one chunk and store it. Idempotent: skip re-embedding known hashes."""
    chunk_text = body["chunk_text"]
    chunk_hash = compute_hash(body["document_id"], body["chunk_index"], chunk_text)

    if repo.exists(chunk_hash):
        logger.info("skip duplicate chunk", extra={"chunk_hash": chunk_hash})
        return "skipped"

    vector = embed_fn([chunk_text])[0]
    repo.insert(
        document_id=UUID(body["document_id"]),
        chunk_text=chunk_text,
        chunk_hash=chunk_hash,
        embedding=vector,
        metadata=body.get("metadata", {}),
    )
    return "stored"


def poll_loop() -> None:  # pragma: no cover - runtime loop, exercised in the container
    sqs = boto3.client(
        "sqs",
        endpoint_url=settings.sqs_endpoint_url or None,
        region_name=settings.aws_region,
    )
    logger.info("embedding worker polling %s", settings.sqs_queue_url)
    while True:
        resp = sqs.receive_message(
            QueueUrl=settings.sqs_queue_url,
            MaxNumberOfMessages=settings.poll_max_messages,
            WaitTimeSeconds=settings.poll_wait_seconds,
        )
        for msg in resp.get("Messages", []):
            try:
                with SessionLocal() as session:
                    handle_message(json.loads(msg["Body"]), ChunkRepository(session), embed)
                sqs.delete_message(
                    QueueUrl=settings.sqs_queue_url, ReceiptHandle=msg["ReceiptHandle"]
                )
            except Exception:
                logger.exception("failed to process message; leaving it on the queue")
