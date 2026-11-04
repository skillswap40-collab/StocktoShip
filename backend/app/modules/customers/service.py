"""Business logic for customers: registration, edits, search, and the audited tax ID reveal."""

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import crypto
from app.modules.audit import service as audit
from app.modules.customers.models import Customer, CustomerStatus
from app.modules.customers.schemas import CustomerCreate, CustomerUpdate, format_ein

# Fields that cannot be cleared; an explicit null for them in an update is ignored.
_REQUIRED_FIELDS = {
    "business_name",
    "owner_name",
    "tax_id",
    "address_line1",
    "city",
    "state",
    "postal_code",
    "status",
}


class DuplicateTaxId(Exception):
    def __init__(self, account_number: str | None):
        super().__init__(account_number)
        self.account_number = account_number


def get_by_tax_id_hash(db: Session, tax_id_hash: str) -> Customer | None:
    return db.scalar(select(Customer).where(Customer.tax_id_hash == tax_id_hash))


def _set_tax_id(customer: Customer, digits: str) -> None:
    customer.tax_id_encrypted = crypto.encrypt(digits)
    customer.tax_id_hash = crypto.fingerprint(digits)
    customer.tax_id_last4 = digits[-4:]


def register(db: Session, data: CustomerCreate, actor_id: int | None) -> Customer:
    existing = get_by_tax_id_hash(db, crypto.fingerprint(data.tax_id))
    if existing is not None:
        raise DuplicateTaxId(existing.account_number)

    customer = Customer(
        **data.model_dump(exclude={"tax_id"}),
        registered_by_user_id=actor_id,
    )
    _set_tax_id(customer, data.tax_id)
    db.add(customer)
    try:
        db.flush()
    except IntegrityError:
        # Two registers raced past the pre-check; the unique constraint caught the second.
        db.rollback()
        raise DuplicateTaxId(None) from None
    db.refresh(customer)  # load the database-generated account number
    audit.record(
        db,
        action="customer.created",
        entity_type="customer",
        entity_id=customer.id,
        actor_user_id=actor_id,
        details={"account_number": customer.account_number},
    )
    db.commit()
    return customer


def update(db: Session, customer: Customer, data: CustomerUpdate, actor_id: int) -> Customer:
    changed: set[str] = set()
    for field, value in data.model_dump(exclude_unset=True).items():
        if value is None and field in _REQUIRED_FIELDS:
            continue
        if field == "tax_id":
            new_hash = crypto.fingerprint(value)
            if new_hash == customer.tax_id_hash:
                continue
            other = get_by_tax_id_hash(db, new_hash)
            if other is not None:
                raise DuplicateTaxId(other.account_number)
            _set_tax_id(customer, value)
            changed.add(field)
            continue
        if isinstance(value, CustomerStatus):
            value = value.value
        if getattr(customer, field) != value:
            setattr(customer, field, value)
            changed.add(field)

    if not changed:
        return customer
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise DuplicateTaxId(None) from None
    audit.record(
        db,
        action="customer.updated",
        entity_type="customer",
        entity_id=customer.id,
        actor_user_id=actor_id,
        details={"fields": sorted(changed)},  # names only, never values
    )
    db.commit()
    db.refresh(customer)
    return customer


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def search(
    db: Session,
    q: str | None = None,
    status: CustomerStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Customer], int]:
    conditions = []
    if q and q.strip():
        pattern = f"%{_escape_like(q.strip())}%"
        conditions.append(
            or_(
                *(
                    col.ilike(pattern, escape="\\")
                    for col in (
                        Customer.business_name,
                        Customer.owner_name,
                        Customer.account_number,
                        Customer.phone,
                    )
                )
            )
        )
    if status is not None:
        conditions.append(Customer.status == status.value)

    total = db.scalar(select(func.count()).select_from(Customer).where(*conditions))
    rows = db.scalars(
        select(Customer)
        .where(*conditions)
        .order_by(func.lower(Customer.business_name), Customer.id)
        .limit(limit)
        .offset(offset)
    ).all()
    return list(rows), total or 0


def reveal_tax_id(db: Session, customer: Customer, actor_id: int) -> str:
    digits = crypto.decrypt(customer.tax_id_encrypted)
    audit.record(
        db,
        action="customer.tax_id_viewed",
        entity_type="customer",
        entity_id=customer.id,
        actor_user_id=actor_id,
    )
    db.commit()
    return format_ein(digits)
