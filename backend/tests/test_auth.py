"""Login, tokens and the current-user endpoint."""

from app.core.security import create_access_token
from tests.conftest import PASSWORD


def test_login_returns_token_and_me_works(client, make_user):
    user = make_user("cashier")
    resp = client.post("/auth/login", json={"email": user.email, "password": PASSWORD})
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == user.email
    assert me.json()["role"] == "cashier"
    assert "password_hash" not in me.json()


def test_login_is_case_insensitive_on_email(client, make_user):
    user = make_user("manager", email="Owner@Store.com")
    resp = client.post("/auth/login", json={"email": "OWNER@store.com", "password": PASSWORD})
    assert resp.status_code == 200
    assert user.email == "owner@store.com"


def test_login_records_last_login(client, make_user, db):
    user = make_user("cashier")
    assert user.last_login_at is None
    client.post("/auth/login", json={"email": user.email, "password": PASSWORD})
    db.refresh(user)
    assert user.last_login_at is not None


def test_wrong_password_unknown_email_and_inactive_all_look_the_same(client, make_user):
    active = make_user("cashier")
    inactive = make_user("cashier", is_active=False)
    attempts = [
        {"email": active.email, "password": "wrong-password-123"},
        {"email": "nobody@example.com", "password": PASSWORD},
        {"email": inactive.email, "password": PASSWORD},
    ]
    for body in attempts:
        resp = client.post("/auth/login", json=body)
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid email or password"


def test_me_requires_a_token(client):
    assert client.get("/auth/me").status_code == 401


def test_garbage_token_rejected(client):
    resp = client.get("/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401


def test_expired_token_rejected(client, make_user):
    user = make_user("cashier")
    token = create_access_token(user.id, user.role, minutes=-1)
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_deactivated_user_loses_access_immediately(client, make_user, auth_headers, db):
    user = make_user("cashier")
    headers = auth_headers(user)
    assert client.get("/auth/me", headers=headers).status_code == 200

    user.is_active = False
    db.commit()
    assert client.get("/auth/me", headers=headers).status_code == 401
