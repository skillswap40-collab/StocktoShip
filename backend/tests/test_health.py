from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import get_db
from app.main import app


def test_health_reports_ok_when_database_reachable(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "database": "ok"}


def test_health_reports_503_when_database_down():
    # Point at a port where nothing listens
    dead = sessionmaker(bind=create_engine("postgresql+psycopg://x:x@127.0.0.1:1/none"))

    def broken_db():
        session = dead()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = broken_db
    try:
        resp = TestClient(app).get("/health")
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 503
    assert resp.json()["database"] == "unreachable"
