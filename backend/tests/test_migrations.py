"""Migrations must apply, reverse, and match the models exactly."""

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect

from app.db.models import Base
from tests.conftest import alembic_config


def test_models_match_migrations(migrated_db):
    """Fails if someone changes a model without writing a migration."""
    with migrated_db.connect() as conn:
        ctx = MigrationContext.configure(conn, opts={"compare_type": True})
        diff = compare_metadata(ctx, Base.metadata)
    assert diff == [], f"Models and migrations differ: {diff}"


def test_downgrade_to_base_and_upgrade_again(migrated_db):
    cfg = alembic_config()
    command.downgrade(cfg, "base")
    tables = set(inspect(migrated_db).get_table_names()) - {"alembic_version"}
    assert tables == set(), f"Tables left after downgrade: {tables}"

    command.upgrade(cfg, "head")
    tables = set(inspect(migrated_db).get_table_names())
    assert {"audit_log", "user_account"} <= tables
