"""Staff user accounts.

Customer logins are a separate concern and will live with the customers module.
"""

import enum
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin


class Role(enum.StrEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    SALES_REP = "sales_rep"
    CASHIER = "cashier"
    WAREHOUSE = "warehouse"


ROLE_VALUES = tuple(r.value for r in Role)


class User(IdMixin, TimestampMixin, Base):
    __tablename__ = "user_account"  # "user" is a reserved word in PostgreSQL
    __table_args__ = (
        CheckConstraint(
            "role IN (" + ", ".join(f"'{r}'" for r in ROLE_VALUES) + ")", name="valid_role"
        ),
        CheckConstraint("email = lower(email)", name="email_lowercase"),
    )

    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
