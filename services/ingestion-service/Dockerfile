FROM python:3.12-slim

# tesseract is required by the OCR pipeline (pytesseract is just a wrapper).
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Pre-download nltk sentence model so chunking doesn't fetch at runtime.
RUN uv run --no-dev python -m nltk.downloader -d /usr/share/nltk_data punkt punkt_tab
ENV NLTK_DATA=/usr/share/nltk_data

COPY src/ src/

EXPOSE 8000
CMD ["uv", "run", "--no-dev", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
