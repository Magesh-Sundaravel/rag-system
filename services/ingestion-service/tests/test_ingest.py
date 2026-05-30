def test_ingest_text_file_end_to_end(client):
    content = b"First sentence. Second sentence. Third sentence here."
    r = client.post(
        "/ingest",
        files={"file": ("notes.txt", content, "text/plain")},
    )
    assert r.status_code == 202
    body = r.json()
    assert body["detected_type"] == "text/plain"
    assert body["pipeline"] == "text"
    assert body["strategy_used"] == "sentence"
    assert body["chunk_count"] >= 1

    status = client.get(f"/status/{body['job_id']}")
    assert status.status_code == 200
    assert status.json()["status"] == "queued"


def test_ingest_rejects_empty_file(client):
    r = client.post("/ingest", files={"file": ("empty.txt", b"", "text/plain")})
    assert r.status_code == 400


def test_status_unknown_job_404(client):
    assert client.get("/status/does-not-exist").status_code == 404
