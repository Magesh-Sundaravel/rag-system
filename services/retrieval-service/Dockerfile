FROM python:3.12-slim

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
# --extra ml pulls torch + sentence-transformers for the shared embedder.
RUN uv sync --frozen --no-dev --extra ml

COPY src/ src/

EXPOSE 8000
CMD ["uv", "run", "--no-dev", "--extra", "ml", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
