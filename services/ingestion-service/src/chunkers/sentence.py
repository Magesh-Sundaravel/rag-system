import re

from src.config import settings

_FALLBACK = re.compile(r"(?<=[.!?])\s+")


def _split_sentences(text: str) -> list[str]:
    """Prefer nltk; fall back to regex when punkt data is unavailable (e.g. offline tests)."""
    try:
        from nltk.tokenize import sent_tokenize

        return sent_tokenize(text)
    except (ImportError, LookupError):
        return _FALLBACK.split(text)


def chunk_sentence(text: str, max_chars: int | None = None) -> list[str]:
    """Sentence-aware splitting: pack whole sentences up to max_chars."""
    max_chars = max_chars or settings.sentence_chunk_chars
    text = text.strip()
    if not text:
        return []

    chunks: list[str] = []
    current = ""
    for sentence in _split_sentences(text):
        sentence = sentence.strip()
        if not sentence:
            continue
        if current and len(current) + len(sentence) + 1 > max_chars:
            chunks.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks
