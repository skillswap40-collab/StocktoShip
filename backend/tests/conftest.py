"""Shared test fixtures.

Tests always run against a separate database (TEST_DATABASE_URL), never the
development one. The URL must be set before the app is imported.

- `migrated_db` (once per run): wipes the test schema and applies all Alembic
  migrations, so tests exercise the real migrations, not create_all().
- `db`: a session inside an outer transaction that is rolled back after each
  test, so tests never see each other's data. Code under test may commit;
  those commits become savepoints.
- `client`: a TestClient whose requests use that same session.
"""

import os
from pathlib import Path

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/stocktoship_test",
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["ENVIRONMENT"] = "test"

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parents[1]


def alembic_config() -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    return cfg


def reset_schema(engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(TEST_DATABASE_URL)
    yield eng
    eng.dispose()


@pytest.fixture(scope="session")
def migrated_db(engine):
    reset_schema(engine)
    command.upgrade(alembic_config(), "head")
    yield engine


@pytest.fixture
def db(migrated_db) -> Session:
    connection = migrated_db.connect()
    outer = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        outer.rollback()
        connection.close()


PASSWORD = "correct-horse-battery"


@pytest.fixture
def make_user(db):
    """Create a staff user directly in the database: make_user(role="cashier")."""
    from app.modules.identity import service
    from app.modules.identity.models import Role
    from app.modules.identity.schemas import UserCreate

    counter = {"n": 0}

    def _make(role: str = "admin", email: str | None = None, is_active: bool = True):
        counter["n"] += 1
        data = UserCreate(
            email=email or f"{role}{counter['n']}@example.com",
            full_name=f"Test {role.title()} {counter['n']}",
            password=PASSWORD,
            role=Role(role),
        )
        user = service.create_user(db, data, actor_id=None)
        if not is_active:
            user.is_active = False
            db.commit()
        return user

    return _make


def customer_payload(**overrides) -> dict:
    """A valid POST /customers body. Use example.com: email-validator rejects .test domains."""
    body = {
        "business_name": "Corner Market",
        "owner_name": "Dana Owner",
        "tax_id": "12-3456789",
        "address_line1": "1 Main St",
        "city": "Boston",
        "state": "MA",
        "postal_code": "02108",
        "phone": "617-555-0100",
        "email": "owner@example.com",
    }
    body.update(overrides)
    return body


@pytest.fixture
def make_customer(db):
    """Register a customer through the service, each with a unique tax ID."""
    from app.modules.customers import service
    from app.modules.customers.schemas import CustomerCreate

    counter = {"n": 0}

    def _make(**overrides):
        counter["n"] += 1
        overrides.setdefault("tax_id", f"98{counter['n']:07d}")
        overrides.setdefault("business_name", f"Test Store {counter['n']}")
        return service.register(db, CustomerCreate(**customer_payload(**overrides)), actor_id=None)

    return _make


@pytest.fixture
def auth_headers(client):
    """Log in through the API and return an Authorization header."""

    def _headers(user, password: str = PASSWORD) -> dict:
        resp = client.post("/auth/login", json={"email": user.email, "password": password})
        assert resp.status_code == 200, resp.text
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    return _headers


@pytest.fixture
def client(db) -> TestClient:
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
