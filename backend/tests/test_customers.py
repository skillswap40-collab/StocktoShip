"""Customer registration, search, editing, and tax ID protection."""

import re

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.modules.audit.models import AuditLog
from app.modules.customers import service
from app.modules.customers.schemas import CustomerCreate
from tests.conftest import customer_payload

ALL_ROLES = ["admin", "manager", "sales_rep", "cashier", "warehouse"]
REGISTER_ROLES = ["admin", "manager", "sales_rep", "cashier"]


def audit_entries(db, customer_id, action):
    return db.scalars(
        select(AuditLog).where(
            AuditLog.entity_type == "customer",
            AuditLog.entity_id == str(customer_id),
            AuditLog.action == action,
        )
    ).all()


# --- Registration ---------------------------------------------------------------------------


def test_cashier_registers_customer(client, make_user, auth_headers, db):
    cashier = make_user("cashier")
    resp = client.post("/customers", json=customer_payload(), headers=auth_headers(cashier))
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert re.fullmatch(r"C-\d{6}", body["account_number"])
    assert body["tax_id_masked"] == "•••••6789"
    assert body["registered_by_user_id"] == cashier.id
    assert body["status"] == "active"

    [entry] = audit_entries(db, body["id"], "customer.created")
    assert entry.actor_user_id == cashier.id
    assert entry.details == {"account_number": body["account_number"]}


def test_account_numbers_are_sequential(client, make_user, auth_headers):
    headers = auth_headers(make_user("cashier"))
    a = client.post("/customers", json=customer_payload(tax_id="111111111"), headers=headers)
    b = client.post("/customers", json=customer_payload(tax_id="222222222"), headers=headers)
    first, second = (int(r.json()["account_number"][2:]) for r in (a, b))
    assert second == first + 1


@pytest.mark.parametrize("role", REGISTER_ROLES)
def test_staff_roles_can_register(client, make_user, auth_headers, role):
    resp = client.post("/customers", json=customer_payload(), headers=auth_headers(make_user(role)))
    assert resp.status_code == 201


def test_warehouse_cannot_register_and_anonymous_is_401(client, make_user, auth_headers):
    headers = auth_headers(make_user("warehouse"))
    assert client.post("/customers", json=customer_payload(), headers=headers).status_code == 403
    assert client.post("/customers", json=customer_payload()).status_code == 401


# --- Validation -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field", ["business_name", "owner_name", "tax_id", "address_line1", "city", "postal_code"]
)
def test_missing_required_field_is_422(client, make_user, auth_headers, field):
    body = customer_payload()
    del body[field]
    resp = client.post("/customers", json=body, headers=auth_headers(make_user("cashier")))
    assert resp.status_code == 422


@pytest.mark.parametrize(
    "override",
    [
        {"tax_id": "12-345678"},  # 8 digits
        {"tax_id": "12-34567890"},  # 10 digits
        {"tax_id": "00-0000000"},
        {"tax_id": "AB-3456789"},
        {"tax_id": "EIN123456789"},  # 9 digits plus letters
        {"state": "Mass"},
        {"postal_code": "2108"},
        {"email": "not-an-email"},
        {"business_name": "   "},
    ],
)
def test_invalid_values_are_422(client, make_user, auth_headers, override):
    body = customer_payload(**override)
    resp = client.post("/customers", json=body, headers=auth_headers(make_user("cashier")))
    assert resp.status_code == 422, override


def test_input_is_normalized(client, make_user, auth_headers):
    body = customer_payload(
        business_name="  Corner Market  ",
        state="ma",
        email="Owner@Example.COM",
        tax_id="12 345 6789",
        postal_code="02108-1234",
        phone="  ",
    )
    resp = client.post("/customers", json=body, headers=auth_headers(make_user("cashier")))
    assert resp.status_code == 201, resp.text
    out = resp.json()
    assert out["business_name"] == "Corner Market"
    assert out["state"] == "MA"
    assert out["email"] == "owner@example.com"
    assert out["postal_code"] == "02108-1234"
    assert out["phone"] is None


def test_state_defaults_to_ma(client, make_user, auth_headers):
    body = customer_payload()
    del body["state"]
    resp = client.post("/customers", json=body, headers=auth_headers(make_user("cashier")))
    assert resp.json()["state"] == "MA"


# --- Duplicates -----------------------------------------------------------------------------


def test_duplicate_tax_id_in_another_format_is_409(client, make_user, auth_headers):
    headers = auth_headers(make_user("cashier"))
    first = client.post("/customers", json=customer_payload(tax_id="12-3456789"), headers=headers)
    dup = client.post(
        "/customers",
        json=customer_payload(tax_id="123456789", business_name="Other Store"),
        headers=headers,
    )
    assert dup.status_code == 409
    assert first.json()["account_number"] in dup.json()["detail"]


def test_race_past_precheck_is_caught_by_unique_constraint(db, make_customer, monkeypatch):
    make_customer(tax_id="555555555")
    monkeypatch.setattr(service, "get_by_tax_id_hash", lambda db, h: None)
    with pytest.raises(service.DuplicateTaxId) as exc:
        service.register(db, CustomerCreate(**customer_payload(tax_id="555555555")), actor_id=None)
    assert exc.value.account_number is None


# --- Tax ID protection ----------------------------------------------------------------------


def test_tax_id_is_not_stored_in_plain_text(db, make_customer):
    customer = make_customer(tax_id="12-3456789")
    row = db.execute(text("SELECT * FROM customer WHERE id = :id"), {"id": customer.id}).one()
    dumped = " ".join(str(v) for v in row)
    assert "123456789" not in dumped
    assert "12-3456789" not in dumped
    assert customer.tax_id_last4 == "6789"


@pytest.mark.parametrize("role", ALL_ROLES)
def test_no_role_sees_full_tax_id_in_detail_or_search(
    client, make_user, auth_headers, make_customer, role
):
    customer = make_customer(tax_id="12-3456789")
    headers = auth_headers(make_user(role))
    detail = client.get(f"/customers/{customer.id}", headers=headers)
    search = client.get("/customers", params={"q": customer.business_name}, headers=headers)
    assert detail.status_code == 200 and search.status_code == 200
    assert search.json()["total"] == 1
    for resp in (detail, search):
        assert "3456789" not in resp.text
        assert "tax_id_encrypted" not in resp.text
        assert "tax_id_hash" not in resp.text
    assert detail.json()["tax_id_masked"] == "•••••6789"
    assert "tax_id" not in detail.json()


def test_admin_reveal_is_audited(client, make_user, auth_headers, make_customer, db):
    customer = make_customer(tax_id="123456789")
    admin = make_user("admin")
    resp = client.get(f"/customers/{customer.id}/tax-id", headers=auth_headers(admin))
    assert resp.status_code == 200
    assert resp.json() == {
        "customer_id": customer.id,
        "account_number": customer.account_number,
        "tax_id": "12-3456789",
    }
    [entry] = audit_entries(db, customer.id, "customer.tax_id_viewed")
    assert entry.actor_user_id == admin.id
    assert "3456789" not in str(entry.details)


@pytest.mark.parametrize("role", ["manager", "sales_rep", "cashier", "warehouse"])
def test_non_admin_reveal_is_403_and_not_audited(
    client, make_user, auth_headers, make_customer, db, role
):
    customer = make_customer()
    resp = client.get(f"/customers/{customer.id}/tax-id", headers=auth_headers(make_user(role)))
    assert resp.status_code == 403
    assert audit_entries(db, customer.id, "customer.tax_id_viewed") == []


def test_reveal_unknown_customer_is_404(client, make_user, auth_headers):
    resp = client.get("/customers/999999/tax-id", headers=auth_headers(make_user("admin")))
    assert resp.status_code == 404


# --- Search and view ------------------------------------------------------------------------


@pytest.fixture
def shop_customers(make_customer):
    return {
        "alpha": make_customer(business_name="Alpha Foods", owner_name="Ann Lee", phone="111"),
        "beta": make_customer(business_name="Beta 100% Deli", owner_name="Bob Ray", phone="222"),
        "gamma": make_customer(
            business_name="Gamma_Mart", owner_name="Cal Wu", phone="617-555-0199"
        ),
    }


def names(resp):
    return [c["business_name"] for c in resp.json()["items"]]


@pytest.mark.parametrize("role", ALL_ROLES)
def test_every_role_can_search_and_view(client, make_user, auth_headers, shop_customers, role):
    headers = auth_headers(make_user(role))
    resp = client.get("/customers", headers=headers)
    assert resp.status_code == 200
    assert names(resp) == ["Alpha Foods", "Beta 100% Deli", "Gamma_Mart"]
    alpha = shop_customers["alpha"]
    assert client.get(f"/customers/{alpha.id}", headers=headers).status_code == 200


def test_search_matches_name_owner_account_and_phone(
    client, make_user, auth_headers, shop_customers
):
    headers = auth_headers(make_user("cashier"))

    def search(q):
        return names(client.get("/customers", params={"q": q}, headers=headers))

    assert search("alpha") == ["Alpha Foods"]
    assert search("BOB") == ["Beta 100% Deli"]
    assert search(shop_customers["gamma"].account_number) == ["Gamma_Mart"]
    assert search("555-0199") == ["Gamma_Mart"]


def test_search_treats_wildcards_literally(client, make_user, auth_headers, shop_customers):
    headers = auth_headers(make_user("cashier"))
    assert names(client.get("/customers", params={"q": "%"}, headers=headers)) == ["Beta 100% Deli"]
    assert names(client.get("/customers", params={"q": "_"}, headers=headers)) == ["Gamma_Mart"]
    assert names(client.get("/customers", params={"q": "\\"}, headers=headers)) == []


def test_search_pagination(client, make_user, auth_headers, shop_customers):
    headers = auth_headers(make_user("cashier"))
    page = client.get("/customers", params={"limit": 2, "offset": 0}, headers=headers).json()
    assert page["total"] == 3 and len(page["items"]) == 2
    assert page["limit"] == 2 and page["offset"] == 0
    page = client.get("/customers", params={"limit": 2, "offset": 2}, headers=headers).json()
    assert page["total"] == 3 and [c["business_name"] for c in page["items"]] == ["Gamma_Mart"]
    assert client.get("/customers", params={"limit": 0}, headers=headers).status_code == 422
    assert client.get("/customers", params={"limit": 201}, headers=headers).status_code == 422
    assert client.get("/customers", params={"q": "x" * 101}, headers=headers).status_code == 422


def test_search_status_filter(client, make_user, auth_headers, shop_customers, db):
    shop_customers["beta"].status = "on_hold"
    db.commit()
    headers = auth_headers(make_user("cashier"))
    resp = client.get("/customers", params={"status": "on_hold"}, headers=headers)
    assert names(resp) == ["Beta 100% Deli"]
    resp = client.get("/customers", params={"status": "active"}, headers=headers)
    assert resp.json()["total"] == 2
    assert client.get("/customers", params={"status": "bogus"}, headers=headers).status_code == 422


def test_unknown_customer_is_404(client, make_user, auth_headers):
    resp = client.get("/customers/999999", headers=auth_headers(make_user("cashier")))
    assert resp.status_code == 404


# --- Editing --------------------------------------------------------------------------------


def test_manager_edits_and_audit_has_field_names_only(
    client, make_user, auth_headers, make_customer, db
):
    customer = make_customer()
    manager = make_user("manager")
    resp = client.patch(
        f"/customers/{customer.id}",
        json={"phone": "617-555-0123", "status": "on_hold", "city": "Cambridge"},
        headers=auth_headers(manager),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert (body["phone"], body["status"], body["city"]) == ("617-555-0123", "on_hold", "Cambridge")

    [entry] = audit_entries(db, customer.id, "customer.updated")
    assert entry.actor_user_id == manager.id
    assert entry.details == {"fields": ["city", "phone", "status"]}


@pytest.mark.parametrize("role", ["sales_rep", "cashier", "warehouse"])
def test_other_roles_cannot_edit(client, make_user, auth_headers, make_customer, role):
    customer = make_customer()
    resp = client.patch(
        f"/customers/{customer.id}", json={"city": "Lowell"}, headers=auth_headers(make_user(role))
    )
    assert resp.status_code == 403


def test_manager_cannot_change_tax_id(client, make_user, auth_headers, make_customer, db):
    customer = make_customer(tax_id="123456789")
    resp = client.patch(
        f"/customers/{customer.id}",
        json={"tax_id": "98-7654321"},
        headers=auth_headers(make_user("manager")),
    )
    assert resp.status_code == 403
    db.refresh(customer)
    assert customer.tax_id_last4 == "6789"
    assert audit_entries(db, customer.id, "customer.updated") == []


def test_admin_changes_tax_id(client, make_user, auth_headers, make_customer, db):
    customer = make_customer(tax_id="123456789")
    headers = auth_headers(make_user("admin"))
    resp = client.patch(f"/customers/{customer.id}", json={"tax_id": "98-7654321"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["tax_id_masked"] == "•••••4321"
    reveal = client.get(f"/customers/{customer.id}/tax-id", headers=headers)
    assert reveal.json()["tax_id"] == "98-7654321"
    [entry] = audit_entries(db, customer.id, "customer.updated")
    assert entry.details == {"fields": ["tax_id"]}


def test_changing_to_another_customers_tax_id_is_409(
    client, make_user, auth_headers, make_customer
):
    first = make_customer(tax_id="111111111")
    second = make_customer(tax_id="222222222")
    resp = client.patch(
        f"/customers/{second.id}",
        json={"tax_id": "11-1111111"},
        headers=auth_headers(make_user("admin")),
    )
    assert resp.status_code == 409
    assert first.account_number in resp.json()["detail"]


def test_no_op_edit_writes_no_audit(client, make_user, auth_headers, make_customer, db):
    customer = make_customer(tax_id="123456789", city="Boston")
    resp = client.patch(
        f"/customers/{customer.id}",
        json={"city": "Boston", "tax_id": "12-3456789"},
        headers=auth_headers(make_user("admin")),
    )
    assert resp.status_code == 200
    assert audit_entries(db, customer.id, "customer.updated") == []


def test_null_on_required_field_is_ignored(client, make_user, auth_headers, make_customer):
    customer = make_customer(business_name="Keep Me")
    resp = client.patch(
        f"/customers/{customer.id}",
        json={"business_name": None, "status": None, "notes": "Pays on Fridays"},
        headers=auth_headers(make_user("manager")),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["business_name"] == "Keep Me"
    assert body["status"] == "active"
    assert body["notes"] == "Pays on Fridays"


def test_edit_unknown_customer_is_404(client, make_user, auth_headers):
    resp = client.patch(
        "/customers/999999", json={"city": "Lowell"}, headers=auth_headers(make_user("admin"))
    )
    assert resp.status_code == 404


def test_database_rejects_invalid_status(db, make_customer):
    customer = make_customer()
    with pytest.raises(IntegrityError):
        db.execute(
            text("UPDATE customer SET status = 'closed' WHERE id = :id"), {"id": customer.id}
        )
