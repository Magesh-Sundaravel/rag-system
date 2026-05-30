def test_query_streams_then_persists_history(client):
    r = client.post("/query", json={"query": "hi there", "session_id": "s1"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    # Both streamed deltas are present in the SSE body.
    assert "Hello" in r.text
    assert "world" in r.text

    h = client.get("/history/s1")
    assert h.status_code == 200
    items = h.json()
    assert len(items) == 1
    assert items[0]["query"] == "hi there"
    assert items[0]["answer"] == "Hello world"


def test_history_empty_for_unknown_session(client):
    assert client.get("/history/nope").json() == []
