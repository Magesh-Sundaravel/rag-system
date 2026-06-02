from collections.abc import Iterator

from src.config import settings

SYSTEM_PROMPT = (
    "You are a retrieval-augmented assistant. Answer the question using ONLY the "
    "provided context. If the answer is not contained in the context, say you don't "
    "know. Do not use prior knowledge and do not invent facts."
)


def build_messages(query: str, contexts: list[str]) -> list[dict]:
    """Strict RAG prompt. Pure function — unit tested."""
    context_block = "\n\n".join(f"[{i + 1}] {c}" for i, c in enumerate(contexts))
    user = f"Context:\n{context_block}\n\nQuestion: {query}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def stream_answer(query: str, contexts: list[str]) -> Iterator[str]:
    """Stream the Groq completion as text deltas."""
    from groq import Groq

    client = Groq(api_key=settings.groq_api_key)
    stream = client.chat.completions.create(
        model=settings.groq_model,
        messages=build_messages(query, contexts),
        temperature=0,
        stream=True,
        # Required so the final streamed chunk carries token usage, which the
        # OpenLLMetry Groq instrumentor records on the span.
        stream_options={"include_usage": True},
    )
    for chunk in stream:
        # The final usage-only chunk (from include_usage) has no choices.
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
