from src.repository import compute_hash


def test_hash_is_deterministic():
    a = compute_hash("doc1", 0, "hello world")
    b = compute_hash("doc1", 0, "hello world")
    assert a == b


def test_hash_varies_with_text_and_index():
    base = compute_hash("doc1", 0, "hello world")
    assert compute_hash("doc1", 1, "hello world") != base
    assert compute_hash("doc1", 0, "different") != base
    assert compute_hash("doc2", 0, "hello world") != base
