from src.config import settings

# Ordered from coarsest (paragraph) to finest, so we respect headers/sections first.
_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def chunk_recursive(
    text: str, size: int | None = None, separators: list[str] | None = None
) -> list[str]:
    """Recursive character splitting that keeps natural boundaries when possible."""
    size = size or settings.recursive_chunk_chars
    separators = separators if separators is not None else _SEPARATORS
    text = text.strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]

    sep = next((s for s in separators if s == "" or s in text), "")
    if sep == "":
        return [text[i : i + size] for i in range(0, len(text), size)]

    pieces = [p + sep for p in text.split(sep)]
    rest = separators[separators.index(sep) + 1 :]

    chunks: list[str] = []
    current = ""
    for piece in pieces:
        if len(piece) > size:
            if current.strip():
                chunks.append(current.strip())
                current = ""
            chunks.extend(chunk_recursive(piece, size, rest))
        elif len(current) + len(piece) <= size:
            current += piece
        else:
            if current.strip():
                chunks.append(current.strip())
            current = piece
    if current.strip():
        chunks.append(current.strip())
    return chunks
