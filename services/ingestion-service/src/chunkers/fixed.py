from src.config import settings


def chunk_fixed(
    text: str,
    size: int | None = None,
    overlap: int | None = None,
) -> list[str]:
    """Fixed-size sliding window over whitespace tokens (token ~= word).

    Used for OCR output, which is unstructured.
    """
    size = size or settings.fixed_chunk_tokens
    overlap = overlap if overlap is not None else settings.fixed_chunk_overlap
    tokens = text.split()
    if not tokens:
        return []

    step = max(1, size - overlap)
    chunks: list[str] = []
    for start in range(0, len(tokens), step):
        chunks.append(" ".join(tokens[start : start + size]))
        if start + size >= len(tokens):
            break
    return chunks
