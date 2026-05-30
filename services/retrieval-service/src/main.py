import json
from uuid import uuid4

from fastapi import Depends, FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from src import llm, retriever
from src.config import settings
from src.db import get_db
from src.embedder import embed
from src.models import ChatHistory

app = FastAPI(title="retrieval-service")


class QueryRequest(BaseModel):
    query: str
    session_id: str | None = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/query")
def query(body: QueryRequest, db: Session = Depends(get_db)) -> StreamingResponse:
    session_id = body.session_id or str(uuid4())
    contexts = retriever.retrieve(db, body.query, embed, settings.top_k)

    def event_stream():
        parts: list[str] = []
        for delta in llm.stream_answer(body.query, contexts):
            parts.append(delta)
            yield f"data: {json.dumps({'delta': delta})}\n\n"
        answer = "".join(parts)
        db.add(ChatHistory(session_id=session_id, query=body.query, answer=answer))
        db.commit()
        yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/history/{session_id}")
def history(session_id: str, db: Session = Depends(get_db)) -> list[dict]:
    stmt = (
        select(ChatHistory)
        .where(ChatHistory.session_id == session_id)
        .order_by(ChatHistory.created_at)
    )
    return [
        {
            "query": row.query,
            "answer": row.answer,
            "created_at": row.created_at.isoformat(),
        }
        for row in db.scalars(stmt)
    ]
