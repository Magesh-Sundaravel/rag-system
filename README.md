# RAG System

A retrieval-augmented generation platform built as a set of independently deployable
microservices, running on Kubernetes (EKS). Documents are ingested, chunked, embedded
locally, and stored in Postgres with pgvector. Queries run hybrid retrieval (vector
similarity + BM25, combined with reciprocal rank fusion) and stream an answer back
from an LLM, grounded in the retrieved chunks.

Each service owns its own data, its own dependency lockfile, and its own tests. There
is no shared ORM layer and no service reaches into another service's tables.

## Architecture

```
Browser
  |
  v
api-gateway (:8080)  --  single entry point, JWT verification, rate limiting
  |
  |-- /auth/*      -->  auth-service (:8001)       -- users, JWT issuance/refresh
  |-- /ingest      -->  ingestion-service (:8002)  -- chunking, S3 upload, SQS publish
  |-- /status/{id} -->  ingestion-service (:8002)
  |-- /query       -->  retrieval-service (:8004)  -- hybrid search + Groq generation
  |-- /history/*   -->  retrieval-service (:8004)

embedding-service (:8003)  -- SQS consumer, embeds chunks, writes to pgvector
```

| Service | Responsibility | Owns |
|---|---|---|
| `auth-service` | Registration, login, JWT issuance and refresh, token revocation | `users`, `revoked_tokens` |
| `ingestion-service` | Accepts documents, chunks them, uploads raw files to S3, publishes chunk jobs to SQS | — |
| `embedding-service` | Consumes chunk jobs from SQS, embeds with `sentence-transformers`, writes vectors | `document_chunks` (write) |
| `retrieval-service` | Hybrid search over `document_chunks`, prompt construction, Groq generation | `document_chunks` (read) |
| `api-gateway` | Single ingress point, JWT verification, rate limiting, request routing | — |
| `frontend` | Vanilla JS + Tailwind single-page app | — |

Every service is stateless — no local file storage. Raw documents live in S3; all
structured data lives in Postgres. Locally, all services share one Postgres instance
via `docker-compose`; in production they may be split across databases without any
code changes, since a service only ever queries the tables it owns.

## Why these choices

- **Embeddings run locally, not through Groq.** Groq does not serve an embeddings
  API, so chunks are embedded with `sentence-transformers` (`BAAI/bge-large-en-v1.5`,
  1024 dimensions). The embedding model is shared between `embedding-service` and
  `retrieval-service` so that stored vectors and query vectors always live in the
  same space.
- **Groq is used only for generation**, with `llama-3.3-70b-versatile` as the default
  model.
- **SQS decouples ingestion from embedding.** Chunking and embedding have very
  different latency and resource profiles (embedding needs a GPU-friendly runtime
  with `torch`), so they run as separate services connected by a queue rather than
  a single synchronous pipeline.
- **Hybrid retrieval.** Pure vector search misses exact keyword matches (IDs, error
  codes, proper nouns). Retrieval combines vector similarity with BM25 and merges
  the two rankings with reciprocal rank fusion before generation.

## Repository layout

```
services/
  auth-service/         FastAPI, SQLAlchemy, Postgres, JWT
  ingestion-service/    FastAPI, chunking, boto3 (S3 + SQS)
  embedding-service/    SQS consumer, sentence-transformers, pgvector writes
  retrieval-service/    FastAPI, hybrid search, Groq client, streaming responses
  api-gateway/          FastAPI, JWT verification, rate limiting, reverse proxy
frontend/               Vanilla JS + Tailwind SPA
infra/postgres/         Schema init SQL (pgvector extension, tables)
k8s/                     Per-service manifests, HPAs, ingress, external secrets
.github/workflows/       CI (lint + test per service) and CD (build, push, deploy)
docker-compose.yml       Local infra only: Postgres+pgvector, LocalStack, OTel stack
```

Each service directory is a self-contained Python project: its own `pyproject.toml`,
`uv.lock`, `ruff.toml`, `src/`, `tests/`, and `Dockerfile`.

## Running locally

Full walkthrough, including LocalStack setup and a Groq API key, is in
[`run-locally.md`](./run-locally.md). Short version:

```bash
docker compose up -d                     # Postgres+pgvector, LocalStack, OTel stack

uv run --directory services/auth-service       uvicorn src.main:app --port 8001 --reload
uv run --directory services/ingestion-service  uvicorn src.main:app --port 8002 --reload
uv run --extra ml --directory services/embedding-service  uvicorn src.main:app --port 8003 --reload
uv run --extra ml --directory services/retrieval-service  uvicorn src.main:app --port 8004 --reload
uv run --directory services/api-gateway         uvicorn src.main:app --port 8080 --reload
```

Serve the frontend separately:

```bash
cd frontend && python3 -m http.server 5500
```

## Testing and linting

Each service is tested and linted in isolation:

```bash
uv run --directory services/<service> ruff check .
uv run --directory services/<service> ruff format --check .
uv run --directory services/<service> pytest
```

CI runs this matrix across all five Python services plus a syntax check on the
frontend, on every pull request.

## Observability

All services emit OpenTelemetry traces, metrics, and logs via OTLP. Locally these
go to `grafana/otel-lgtm` (Grafana at `http://localhost:3000`, no login). In
production, the collector runs as its own deployment in-cluster
(`k8s/observability/`). See [`OBSERVABILITY_WALKTHROUGH.md`](./OBSERVABILITY_WALKTHROUGH.md)
for a guided tour of what's instrumented and how to read it.

## Deployment

CI/CD is GitHub Actions: pull requests run lint and test per service; pushes to
`main` build all six images, push them to ECR, and apply the Kubernetes manifests
to EKS (`.github/workflows/ci.yaml`, `.github/workflows/cd.yaml`).

The application code and manifests are complete, but this has not yet been deployed
to an AWS account — no VPC, EKS cluster, ECR repositories, or IAM roles are
provisioned, and the required GitHub Actions secrets/variables are not set. See
[`deployment.md`](./deployment.md) for the exact list of what's outstanding and the
order to provision it in.

## Secrets

Groq API keys, database passwords, and JWT signing secrets are never committed or
logged. Locally they're supplied via environment variables; in EKS they're pulled
from AWS Secrets Manager through the External Secrets Operator
(`k8s/external-secrets/`).
