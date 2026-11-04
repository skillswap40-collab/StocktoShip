"""Customer businesses (stores), registered on site by staff.

The tax ID is stored three ways, none of them plain text:
- `tax_id_encrypted`: Fernet ciphertext, decrypted only for the admin reveal endpoint
- `tax_id_hash`: keyed HMAC, unique, so duplicates are caught without decrypting
- `tax_id_last4`: for the masked display every staff role sees
"""

import enum

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Sequence, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin

# Created by hand in the migration; autogenerate does not emit sequences.
account_seq = Sequence("customer_account_seq", metadata=Base.metadata)


class CustomerStatus(enum.StrEnum):
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    INACTIVE = "inactive"


STATUS_VALUES = tuple(s.value for s in CustomerStatus)


class Customer(IdMixin, TimestampMixin, Base):
    __tablename__ = "customer"
    __table_args__ = (
        CheckConstraint(
            "status IN (" + ", ".join(f"'{s}'" for s in STATUS_VALUES) + ")", name="valid_status"
        ),
        CheckConstraint("tax_id_last4 ~ '^[0-9]{4}$'", name="tax_id_last4_digits"),
        CheckConstraint("state ~ '^[A-Z]{2}$'", name="state_code"),
    )

    account_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        server_default=text("'C-' || lpad(nextval('customer_account_seq')::text, 6, '0')"),
    )
    business_name: Mapped[str] = mapped_column(String(200), nullable=False)
    owner_name: Mapped[str] = mapped_column(String(120), nullable=False)

    tax_id_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    tax_id_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    tax_id_last4: Mapped[str] = mapped_column(String(4), nullable=False)

    address_line1: Mapped[str] = mapped_column(String(200), nullable=False)
    address_line2: Mapped[str | None] = mapped_column(String(200), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(2), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(10), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)

    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="active")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Nullable: CSV imports and system jobs register customers without a signed-in user.
    registered_by_user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("user_account.id", ondelete="RESTRICT"), nullable=True
    )

    @property
    def tax_id_masked(self) -> str:
        return "•••••" + self.tax_id_last4
