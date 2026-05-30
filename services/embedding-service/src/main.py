import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import settings
from src.consumer import poll_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run the SQS consumer alongside the health endpoint. Skipped when no queue configured.
    if settings.sqs_queue_url:
        threading.Thread(target=poll_loop, daemon=True).start()
    yield


app = FastAPI(title="embedding-service", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
