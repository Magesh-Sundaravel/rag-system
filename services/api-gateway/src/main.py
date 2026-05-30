from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from src import proxy
from src.config import settings
from src.security import require_jwt

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tests may pre-set proxy.client with a mock transport; don't clobber it.
    if proxy.client is None:
        proxy.client = httpx.AsyncClient(timeout=settings.request_timeout_seconds)
    yield
    await proxy.client.aclose()


app = FastAPI(title="api-gateway", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


# --- auth: public passthrough ---
@app.api_route("/auth/{path:path}", methods=["GET", "POST"])
async def auth_proxy(path: str, request: Request):
    return await proxy.forward(request, f"{settings.auth_url}/{path}")


# --- ingestion: JWT required ---
@app.post("/ingest")
async def ingest_proxy(request: Request, _: dict = Depends(require_jwt)):
    return await proxy.forward(request, f"{settings.ingestion_url}/ingest")


@app.get("/status/{job_id}")
async def status_proxy(job_id: str, request: Request, _: dict = Depends(require_jwt)):
    return await proxy.forward(request, f"{settings.ingestion_url}/status/{job_id}")


# --- retrieval: JWT required ---
@app.post("/query")
async def query_proxy(request: Request, _: dict = Depends(require_jwt)):
    return await proxy.stream(request, f"{settings.retrieval_url}/query")


@app.get("/history/{session_id}")
async def history_proxy(session_id: str, request: Request, _: dict = Depends(require_jwt)):
    return await proxy.forward(request, f"{settings.retrieval_url}/history/{session_id}")
