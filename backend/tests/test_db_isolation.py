"""Each test runs in its own rolled-back transaction."""

from sqlalchemy import func, select

from app.modules.audit import service as audit
from app.modules.audit.models import AuditLog


def test_write_is_visible_inside_the_test(db):
    audit.record(db, action="test.write", entity_type="test", entity_id=1)
    db.commit()  # becomes a savepoint; the outer transaction is rolled back later
    count = db.scalar(select(func.count()).select_from(AuditLog))
    assert count == 1


def test_previous_test_data_is_gone(db):
    count = db.scalar(select(func.count()).select_from(AuditLog))
    assert count == 0


def test_audit_entry_has_defaults(db):
    entry = audit.record(db, action="x", entity_type="y")
    db.flush()
    db.refresh(entry)
    assert entry.id is not None
    assert entry.occurred_at is not None
    assert entry.details == {}
