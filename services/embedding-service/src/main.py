import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import settings
from src.consumer import poll_loop
from src.db import engine
from src.telemetry import init_telemetry


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run the SQS consumer alongside the health endpoint. Skipped when no queue configured.
    if settings.sqs_queue_url:
        threading.Thread(target=poll_loop, daemon=True).start()
    yield


app = FastAPI(title="embedding-service", lifespan=lifespan)

if init_telemetry(app, service_name="embedding-service", engine=engine):
    # Trace boto3 SQS calls made by the consumer thread.
    from opentelemetry.instrumentation.botocore import BotocoreInstrumentor

    BotocoreInstrumentor().instrument()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
