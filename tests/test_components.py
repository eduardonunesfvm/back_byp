import pytest

from app.core import security
from app.models.user import User

CPU = {
    "name": "AMD Ryzen 5 5600",
    "category": "cpu",
    "brand": "AMD",
    "price": 899.0,
    "specs": {"cores": 6, "socket": "AM4"},
}


def _make_user(db_session, username, email, is_admin=False):
    user = User(
        email=email,
        username=username,
        password_hash=security.hash_password("senha12345"),
        is_admin=is_admin,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _headers_for(user):
    token = security.create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin(client, db_session):
    return _make_user(db_session, "admin", "admin@test.com", is_admin=True)


@pytest.fixture()
def regular(client, db_session):
    return _make_user(db_session, "regular", "regular@test.com")


def test_list_empty(client):
    resp = client.get("/api/v1/components")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_missing_returns_404(client):
    resp = client.get("/api/v1/components/9999")
    assert resp.status_code == 404


def test_create_requires_admin(client, regular, admin):
    resp_no_token = client.post("/api/v1/components", json=CPU)
    assert resp_no_token.status_code == 401

    resp_regular = client.post("/api/v1/components", json=CPU, headers=_headers_for(regular))
    assert resp_regular.status_code == 403

    resp_admin = client.post("/api/v1/components", json=CPU, headers=_headers_for(admin))
    assert resp_admin.status_code == 201


def test_crud_flow(client, admin):
    headers = _headers_for(admin)

    created = client.post("/api/v1/components", json=CPU, headers=headers)
    assert created.status_code == 201
    comp_id = created.json()["id"]

    listed = client.get("/api/v1/components")
    assert any(c["id"] == comp_id for c in listed.json())

    filtered = client.get("/api/v1/components", params={"category": "cpu"})
    assert any(c["id"] == comp_id for c in filtered.json())

    not_matched = client.get("/api/v1/components", params={"category": "gpu"})
    assert all(c["id"] != comp_id for c in not_matched.json())

    updated = client.put(
        f"/api/v1/components/{comp_id}",
        json={"price": 999.0},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["price"] == 999.0

    deleted = client.delete(f"/api/v1/components/{comp_id}", headers=headers)
    assert deleted.status_code == 204

    gone = client.get(f"/api/v1/components/{comp_id}")
    assert gone.status_code == 404


def test_invalid_category_422(client, admin):
    resp = client.post(
        "/api/v1/components",
        json={**CPU, "category": "placa-video"},
        headers=_headers_for(admin),
    )
    assert resp.status_code == 422