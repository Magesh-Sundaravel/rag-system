from src.retriever import rrf_fuse


def test_rrf_rewards_agreement_across_lists():
    # "b" is high in both lists -> should win even though "a" tops the first.
    vector = ["a", "b", "c"]
    keyword = ["b", "d", "a"]
    fused = rrf_fuse([vector, keyword], k=60)
    assert fused[0] == "b"
    assert set(fused) == {"a", "b", "c", "d"}


def test_rrf_single_list_preserves_order():
    assert rrf_fuse([["x", "y", "z"]]) == ["x", "y", "z"]


def test_rrf_empty():
    assert rrf_fuse([]) == []
