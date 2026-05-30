FROM python:3.12-slim

# uv for fast, reproducible installs.
RUN pip install --no-cache-dir uv

WORKDIR /app

# Install deps first (cached layer). --frozen requires uv.lock.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src/ src/

EXPOSE 8000
CMD ["uv", "run", "--no-dev", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
