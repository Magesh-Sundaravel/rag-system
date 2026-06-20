from types import SimpleNamespace

from src import llm
from src.llm import SYSTEM_PROMPT, build_messages


def _chunk(content):
    # content=None marks the final usage-only chunk: choices is empty.
    if content is None:
        return SimpleNamespace(choices=[])
    delta = SimpleNamespace(content=content)
    return SimpleNamespace(choices=[SimpleNamespace(delta=delta)])


def test_stream_answer_skips_usage_only_final_chunk(monkeypatch):
    chunks = [_chunk("Hello"), _chunk(" world"), _chunk(None)]

    class FakeGroq:
        def __init__(self, *a, **k):
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=lambda *a, **k: iter(chunks))
            )

    monkeypatch.setattr("groq.Groq", FakeGroq)

    # The empty-choices final chunk must not raise and must not yield text.
    assert list(llm.stream_answer("q", ["ctx"])) == ["Hello", " world"]


def test_build_messages_is_grounded():
    msgs = build_messages("What is X?", ["X is a thing.", "More about X."])
    assert msgs[0]["role"] == "system"
    assert msgs[0]["content"] == SYSTEM_PROMPT
    assert "only the" in SYSTEM_PROMPT.lower()

    user = msgs[1]["content"]
    assert "What is X?" in user
    assert "X is a thing." in user
    assert "More about X." in user
