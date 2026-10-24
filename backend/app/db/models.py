"""Import every model module here so Alembic and tests see the full schema."""

from app.db.base import Base
from app.modules.audit import models as audit_models  # noqa: F401
from app.modules.identity import models as identity_models  # noqa: F401

__all__ = ["Base"]
