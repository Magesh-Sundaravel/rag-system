from src.security import ACCESS, decode_token


def test_register_and_login_returns_valid_jwt(client):
    r = client.post("/register", json={"email": "a@b.com", "password": "secret123"})
    assert r.status_code == 201

    r = client.post("/login", json={"email": "a@b.com", "password": "secret123"})
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"

    claims = decode_token(body["access_token"])
    assert claims["type"] == ACCESS
    assert claims["sub"]


def test_duplicate_register_rejected(client):
    client.post("/register", json={"email": "d@b.com", "password": "secret123"})
    r = client.post("/register", json={"email": "d@b.com", "password": "secret123"})
    assert r.status_code == 400


def test_wrong_password_rejected(client):
    client.post("/register", json={"email": "w@b.com", "password": "secret123"})
    r = client.post("/login", json={"email": "w@b.com", "password": "wrong-pass"})
    assert r.status_code == 401


def test_refresh_then_logout_revokes(client):
    client.post("/register", json={"email": "r@b.com", "password": "secret123"})
    tokens = client.post("/login", json={"email": "r@b.com", "password": "secret123"}).json()
    rt = tokens["refresh_token"]

    assert client.post("/refresh", json={"refresh_token": rt}).status_code == 200
    assert client.post("/logout", json={"refresh_token": rt}).status_code == 204
    # Revoked refresh token can no longer be used.
    assert client.post("/refresh", json={"refresh_token": rt}).status_code == 401
