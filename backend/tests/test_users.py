"""Staff account management and role enforcement."""

import pytest
from sqlalchemy import select

from app.modules.audit.models import AuditLog

NEW_USER = {
    "email": "New.Cashier@example.com",
    "full_name": "New Cashier",
    "password": "a-long-enough-password",
    "role": "cashier",
}


def test_admin_creates_user_and_it_is_audited(client, make_user, auth_headers, db):
    admin = make_user("admin")
    resp = client.post("/users", json=NEW_USER, headers=auth_headers(admin))
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "new.cashier@example.com"
    assert body["role"] == "cashier"
    assert "password" not in body and "password_hash" not in body

    entry = db.scalar(select(AuditLog).where(AuditLog.entity_id == str(body["id"])))
    assert entry.action == "user.created"
    assert entry.actor_user_id == admin.id

    # The new user can log in
    login = client.post(
        "/auth/login", json={"email": NEW_USER["email"], "password": NEW_USER["password"]}
    )
    assert login.status_code == 200


@pytest.mark.parametrize("role", ["manager", "sales_rep", "cashier", "warehouse"])
def test_non_admins_cannot_create_users(client, make_user, auth_headers, role):
    user = make_user(role)
    resp = client.post("/users", json=NEW_USER, headers=auth_headers(user))
    assert resp.status_code == 403


def test_duplicate_email_rejected(client, make_user, auth_headers):
    admin = make_user("admin")
    headers = auth_headers(admin)
    assert client.post("/users", json=NEW_USER, headers=headers).status_code == 201
    dup = dict(NEW_USER, email="NEW.CASHIER@example.com")
    assert client.post("/users", json=dup, headers=headers).status_code == 409


def test_short_password_and_bad_role_rejected(client, make_user, auth_headers):
    headers = auth_headers(make_user("admin"))
    short = dict(NEW_USER, password="short")
    assert client.post("/users", json=short, headers=headers).status_code == 422
    bad_role = dict(NEW_USER, role="superuser")
    assert client.post("/users", json=bad_role, headers=headers).status_code == 422


def test_list_users_allowed_for_admin_and_manager_only(client, make_user, auth_headers):
    make_user("cashier")
    for role, expected in [("admin", 200), ("manager", 200), ("cashier", 403), ("sales_rep", 403)]:
        resp = client.get("/users", headers=auth_headers(make_user(role)))
        assert resp.status_code == expected, role


def test_admin_changes_role_and_deactivates(client, make_user, auth_headers):
    admin = make_user("admin")
    target = make_user("cashier")
    headers = auth_headers(admin)

    resp = client.patch(f"/users/{target.id}", json={"role": "manager"}, headers=headers)
    assert resp.status_code == 200 and resp.json()["role"] == "manager"

    resp = client.patch(f"/users/{target.id}", json={"is_active": False}, headers=headers)
    assert resp.status_code == 200 and resp.json()["is_active"] is False
    login = client.post("/auth/login", json={"email": target.email, "password": "x" * 12})
    assert login.status_code == 401


def test_cannot_remove_last_active_admin(client, make_user, auth_headers):
    admin = make_user("admin")
    headers = auth_headers(admin)
    resp = client.patch(f"/users/{admin.id}", json={"role": "cashier"}, headers=headers)
    assert resp.status_code == 409
    resp = client.patch(f"/users/{admin.id}", json={"is_active": False}, headers=headers)
    assert resp.status_code == 409

    # With a second admin it is allowed
    make_user("admin")
    resp = client.patch(f"/users/{admin.id}", json={"role": "manager"}, headers=headers)
    assert resp.status_code == 200


def test_update_unknown_user_is_404(client, make_user, auth_headers):
    headers = auth_headers(make_user())
    resp = client.patch("/users/999999", json={"role": "cashier"}, headers=headers)
    assert resp.status_code == 404


def test_password_change_is_audited_without_the_value(client, make_user, auth_headers, db):
    admin = make_user("admin")
    target = make_user("cashier")
    client.patch(
        f"/users/{target.id}", json={"password": "brand-new-password"}, headers=auth_headers(admin)
    )
    entry = db.scalar(
        select(AuditLog).where(
            AuditLog.action == "user.updated", AuditLog.entity_id == str(target.id)
        )
    )
    assert entry.details == {"password": "changed"}
