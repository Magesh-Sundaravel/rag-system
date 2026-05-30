from src.llm import SYSTEM_PROMPT, build_messages


def test_build_messages_is_grounded():
    msgs = build_messages("What is X?", ["X is a thing.", "More about X."])
    assert msgs[0]["role"] == "system"
    assert msgs[0]["content"] == SYSTEM_PROMPT
    assert "only the" in SYSTEM_PROMPT.lower()

    user = msgs[1]["content"]
    assert "What is X?" in user
    assert "X is a thing." in user
    assert "More about X." in user
