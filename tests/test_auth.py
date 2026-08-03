from app.core import security
from app.models.user import User

VALID_USER = {
    "email": "user@test.com",
    "username": "user1",
    "password": "senha12345",
}


def _register(client, payload=None):
    return client.post("/api/v1/auth/register", json=payload or VALID_USER)


def _login(client, username, password):
    return client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )


def test_register_ok(client):
    resp = _register(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == VALID_USER["email"]
    assert body["username"] == VALID_USER["username"]
    assert "password" not in body


def test_register_duplicate_email(client):
    _register(client)
    resp = _register(client, {**VALID_USER, "username": "user2"})
    assert resp.status_code == 409


def test_register_duplicate_username(client):
    _register(client)
    resp = _register(client, {**VALID_USER, "email": "outro@test.com"})
    assert resp.status_code == 409


def test_register_short_password(client):
    resp = _register(client, {**VALID_USER, "password": "123"})
    assert resp.status_code == 422


def test_login_ok(client):
    _register(client)
    resp = _login(client, VALID_USER["username"], VALID_USER["password"])
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


def test_login_by_email(client):
    _register(client)
    resp = _login(client, VALID_USER["email"], VALID_USER["password"])
    assert resp.status_code == 200


def test_login_wrong_password(client):
    _register(client)
    resp = _login(client, VALID_USER["username"], "senha-errada")
    assert resp.status_code == 401


def test_me(client):
    _register(client)
    tokens = _login(client, VALID_USER["username"], VALID_USER["password"]).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == VALID_USER["username"]


def test_me_unauthorized(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_refresh_rotates_token(client):
    _register(client)
    refresh_token = _login(client, VALID_USER["username"], VALID_USER["password"]).json()["refresh_token"]
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    new_refresh = resp.json()["refresh_token"]
    assert new_refresh != refresh_token
    # token antigo deve estar revogado
    resp2 = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp2.status_code == 401


def test_refresh_invalid_token(client):
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": "token-inexistente"})
    assert resp.status_code == 401


def test_logout_revokes_refresh(client):
    _register(client)
    tokens = _login(client, VALID_USER["username"], VALID_USER["password"]).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = client.post("/api/v1/auth/logout", headers=headers)
    assert resp.status_code == 204
    resp2 = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp2.status_code == 401