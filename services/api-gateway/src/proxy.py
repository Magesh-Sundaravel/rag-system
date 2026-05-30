import httpx
from fastapi import Request
from fastapi.responses import Response, StreamingResponse
from starlette.background import BackgroundTask

# Set in the app lifespan (or by tests). Module-level so it can be swapped in tests.
client: httpx.AsyncClient | None = None

_HOP_BY_HOP = {
    "host",
    "content-length",
    "connection",
    "keep-alive",
    "transfer-encoding",
}


def _downstream_headers(request: Request) -> dict[str, str]:
    # Forward everything except hop-by-hop headers; this carries Authorization downstream.
    return {k: v for k, v in request.headers.items() if k.lower() not in _HOP_BY_HOP}


async def forward(request: Request, target: str) -> Response:
    """Buffered proxy for JSON endpoints."""
    body = await request.body()
    resp = await client.request(
        request.method,
        target,
        headers=_downstream_headers(request),
        params=dict(request.query_params),
        content=body,
    )
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type"),
    )


async def stream(request: Request, target: str) -> StreamingResponse:
    """Streaming proxy for SSE (/query). Passes bytes through as they arrive."""
    body = await request.body()
    req = client.build_request(
        request.method,
        target,
        headers=_downstream_headers(request),
        params=dict(request.query_params),
        content=body,
    )
    resp = await client.send(req, stream=True)
    return StreamingResponse(
        resp.aiter_raw(),
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type"),
        background=BackgroundTask(resp.aclose),
    )
