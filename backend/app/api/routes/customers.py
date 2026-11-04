"""Customer registration, lookup and editing.

Every staff role sees customer details with the tax ID masked. Admins can reveal the full tax ID
through a separate endpoint, and each reveal is audit-logged.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.modules.customers import service
from app.modules.customers.models import Customer, CustomerStatus
from app.modules.customers.schemas import (
    CustomerCreate,
    CustomerOut,
    CustomerPage,
    CustomerUpdate,
    TaxIdReveal,
)
from app.modules.identity.models import Role, User

router = APIRouter(prefix="/customers", tags=["customers"])

_REGISTER_ROLES = (Role.ADMIN, Role.MANAGER, Role.SALES_REP, Role.CASHIER)


def _get_or_404(db: Session, customer_id: int) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer


def _duplicate(exc: service.DuplicateTaxId) -> HTTPException:
    detail = "A customer with this tax ID already exists"
    if exc.account_number:
        detail += f" ({exc.account_number})"
    return HTTPException(status.HTTP_409_CONFLICT, detail=detail)


@router.post("", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
def register_customer(
    body: CustomerCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(*_REGISTER_ROLES)),
) -> Customer:
    try:
        return service.register(db, body, actor_id=actor.id)
    except service.DuplicateTaxId as exc:
        raise _duplicate(exc) from None


@router.get("", response_model=CustomerPage)
def search_customers(
    q: str | None = Query(default=None, max_length=100),
    status_filter: CustomerStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> CustomerPage:
    rows, total = service.search(db, q=q, status=status_filter, limit=limit, offset=offset)
    return CustomerPage(items=rows, total=total, limit=limit, offset=offset)


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Customer:
    return _get_or_404(db, customer_id)


@router.get("/{customer_id}/tax-id", response_model=TaxIdReveal)
def reveal_tax_id(
    customer_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(Role.ADMIN)),
) -> TaxIdReveal:
    customer = _get_or_404(db, customer_id)
    tax_id = service.reveal_tax_id(db, customer, actor_id=actor.id)
    return TaxIdReveal(
        customer_id=customer.id, account_number=customer.account_number, tax_id=tax_id
    )


@router.patch("/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: int,
    body: CustomerUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(Role.ADMIN, Role.MANAGER)),
) -> Customer:
    if "tax_id" in body.model_fields_set and actor.role != Role.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Only admins can change the tax ID")
    customer = _get_or_404(db, customer_id)
    try:
        return service.update(db, customer, body, actor_id=actor.id)
    except service.DuplicateTaxId as exc:
        raise _duplicate(exc) from None
