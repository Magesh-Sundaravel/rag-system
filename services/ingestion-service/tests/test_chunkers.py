from src.chunkers.fixed import chunk_fixed
from src.chunkers.recursive import chunk_recursive
from src.chunkers.sentence import chunk_sentence


def test_fixed_overlaps_and_covers_all_tokens():
    words = [f"w{i}" for i in range(120)]
    chunks = chunk_fixed(" ".join(words), size=50, overlap=10)
    assert len(chunks) == 3  # step=40 -> starts 0,40,80
    assert chunks[0].split()[:1] == ["w0"]
    assert chunks[-1].split()[-1] == "w119"


def test_fixed_empty():
    assert chunk_fixed("   ") == []


def test_recursive_respects_size():
    text = "\n\n".join(f"sentence number {i} here." for i in range(50))
    chunks = chunk_recursive(text, size=100)
    assert len(chunks) > 1
    assert all(len(c) <= 100 for c in chunks)


def test_sentence_packs_under_limit():
    text = "First sentence. Second sentence. Third one here. Fourth and last."
    one = chunk_sentence(text, max_chars=1000)
    assert one == [text.replace("  ", " ")] or len(one) == 1
    many = chunk_sentence(text, max_chars=20)
    assert len(many) > 1
