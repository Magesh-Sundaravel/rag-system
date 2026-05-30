# RAG System — Project Conventions

Production-grade RAG system, monorepo, microservices, deployed to AWS EKS.

## Architecture decisions (locked)

- **Monorepo** at `rag-system/` root (the "one repo per service" wording in the
  original brief is superseded by this monorepo — CI/CD and `kubectl apply -f k8s/`
  assume a single repo).
- **Embeddings:** Groq does **not** serve embeddings. We embed locally with
  `sentence-transformers` model `BAAI/bge-large-en-v1.5` → **1024 dims**.
  The pgvector column is `vector(1024)` everywhere. Do not write `vector(1536)`.
- **Groq** is used only for **LLM generation** (retrieval-service). Default model:
  `llama-3.3-70b-versatile` (`llama3-70b-8192` is retired).
- **Embedding model is shared** by embedding-service and retrieval-service so the
  query vector and stored vectors live in the same space.

## Service ownership (no cross-service DB access)

| Table | Owner |
|---|---|
| `users`, `revoked_tokens` | auth-service |
| `document_chunks` | embedding-service (write), retrieval-service (read) |

A service only queries its own tables. Locally these share one Postgres instance;
in production they may be separate databases.

## Hard constraints (enforced throughout)

- Every service is **stateless** — no local file storage. Raw files → S3, data → Postgres.
- **Groq API key / DB password / JWT secret** never logged, never in source. Injected
  via env (locally) / AWS Secrets Manager + External Secrets Operator (EKS).
- `ruff check` and `ruff format --check` must pass with **zero warnings** before any commit.
- All chunking decisions logged with `document_id`, `strategy_used`, `chunk_count`.
- Resource requests/limits on every K8s container.

## Tooling

- Python deps via **uv** (each service has its own `pyproject.toml` + `uv.lock`).
- Lint/format via **ruff** (config per service in `ruff.toml`).
- Run a service locally: `uv run --directory services/<svc> uvicorn src.main:app --reload`
- Test a service: `uv run --directory services/<svc> pytest`
- Local infra: `docker compose up -d` (Postgres+pgvector, LocalStack for S3/SQS).

## Build order (execution plan)

1. auth-service ✅  2. Postgres+pgvector ✅  3. ingestion  4. embedding
5. retrieval  6. api-gateway  7. frontend  8. k8s  9. CI/CD
