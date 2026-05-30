from collections.abc import Callable

from src.chunkers.fixed import chunk_fixed
from src.chunkers.recursive import chunk_recursive
from src.chunkers.sentence import chunk_sentence

# Strategy name -> chunker. Selected after document-type detection.
CHUNKERS: dict[str, Callable[[str], list[str]]] = {
    "fixed": chunk_fixed,
    "recursive": chunk_recursive,
    "sentence": chunk_sentence,
}
