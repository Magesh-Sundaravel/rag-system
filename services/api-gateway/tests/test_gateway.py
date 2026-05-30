from tests.conftest import make_token


def test_auth_is_public_passthrough(client):
    r = client.post("/auth/login", json={"email": "a@b.com", "password": "x"})
    assert r.status_code == 200
    assert r.json()["access_token"] == "a"


def test_ingest_requires_jwt(client):
    assert client.post("/ingest", files={"file": ("a.txt", b"hi")}).status_code == 401


def test_ingest_with_valid_jwt(client):
    r = client.post(
        "/ingest",
        files={"file": ("a.txt", b"hi")},
        headers={"Authorization": f"Bearer {make_token()}"},
    )
    assert r.status_code == 202
    assert r.json()["job_id"] == "j1"


def test_query_streams_with_jwt(client):
    r = client.post(
        "/query",
        json={"query": "hi"},
        headers={"Authorization": f"Bearer {make_token()}"},
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    assert "hi" in r.text


def test_invalid_token_rejected(client):
    r = client.post(
        "/query",
        json={"query": "hi"},
        headers={"Authorization": "Bearer not-a-jwt"},
    )
    assert r.status_code == 401


def test_refresh_token_not_accepted_as_access(client):
    r = client.post(
        "/ingest",
        files={"file": ("a.txt", b"hi")},
        headers={"Authorization": f"Bearer {make_token('refresh')}"},
    )
    assert r.status_code == 401
