import json

import boto3

from src.config import settings


def _client():
    return boto3.client(
        "sqs",
        endpoint_url=settings.sqs_endpoint_url or None,
        region_name=settings.aws_region,
    )


def enqueue_chunks(document_id: str, chunks: list[str], metadata: dict) -> None:
    """Send each chunk to SQS for the embedding-service to consume."""
    client = _client()
    for index, text in enumerate(chunks):
        client.send_message(
            QueueUrl=settings.sqs_queue_url,
            MessageBody=json.dumps(
                {
                    "document_id": document_id,
                    "chunk_index": index,
                    "chunk_text": text,
                    "metadata": metadata,
                }
            ),
        )
