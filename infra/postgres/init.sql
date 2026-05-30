-- pgvector + RAG storage. Owned by embedding-service (write) / retrieval-service (read).
-- auth-service manages its own tables (users, revoked_tokens) via SQLAlchemy create_all.

CREATE EXTENSION IF NOT EXISTS vector;

-- Embedding model: BAAI/bge-large-en-v1.5 -> 1024 dimensions.
CREATE TABLE IF NOT EXISTS document_chunks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL,
    chunk_text  TEXT NOT NULL,
    chunk_hash  TEXT UNIQUE NOT NULL,          -- idempotency: skip re-embedding
    embedding   vector(1024),
    metadata    JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx
    ON document_chunks USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS document_chunks_document_id_idx
    ON document_chunks (document_id);

-- BM25 / keyword side of hybrid retrieval.
CREATE INDEX IF NOT EXISTS document_chunks_text_fts_idx
    ON document_chunks USING gin (to_tsvector('english', chunk_text));

-- Chat history. Owned by retrieval-service.
CREATE TABLE IF NOT EXISTS chat_history (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  TEXT NOT NULL,
    query       TEXT NOT NULL,
    answer      TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS chat_history_session_idx
    ON chat_history (session_id, created_at);
