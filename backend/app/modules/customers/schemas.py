"""Request and response shapes for customers.

Responses never carry the full tax ID: only `tax_id_masked`. Admins get the full value from a
separate, audited reveal endpoint (`TaxIdReveal`).
"""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.modules.customers.models import CustomerStatus

_ZIP_RE = re.compile(r"^\d{5}(-\d{4})?$")
_STATE_RE = re.compile(r"^[A-Z]{2}$")
_OPTIONAL_TEXT = ("address_line2", "phone", "email", "notes")


def normalize_tax_id(value: str) -> str:
    """Accept `12-3456789`, `123456789`, `12 345 6789`; return the 9 digits (EIN)."""
    digits = re.sub(r"\D", "", value)
    # Letters are rejected outright rather than stripped, so "EIN123456789" isn't silently kept.
    if len(digits) != 9 or re.search(r"[A-Za-z]", value):
        raise ValueError("tax ID must be a 9-digit EIN, e.g. 12-3456789")
    if digits == "000000000":
        raise ValueError("tax ID cannot be all zeros")
    return digits


def format_ein(digits: str) -> str:
    return f"{digits[:2]}-{digits[2:]}"


class _CustomerFields(BaseModel):
    """Validators shared by create and update. Update fields may be None (not provided)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator(*_OPTIONAL_TEXT, mode="before", check_fields=False)
    @classmethod
    def blank_to_none(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator("tax_id", check_fields=False)
    @classmethod
    def check_tax_id(cls, v: str | None) -> str | None:
        return None if v is None else normalize_tax_id(v)

    @field_validator("state", check_fields=False)
    @classmethod
    def check_state(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.upper()
        if not _STATE_RE.match(v):
            raise ValueError("state must be a 2-letter code, e.g. MA")
        return v

    @field_validator("postal_code", check_fields=False)
    @classmethod
    def check_zip(cls, v: str | None) -> str | None:
        if v is not None and not _ZIP_RE.match(v):
            raise ValueError("ZIP code must be 12345 or 12345-6789")
        return v

    @field_validator("email", check_fields=False)
    @classmethod
    def lower_email(cls, v: str | None) -> str | None:
        return None if v is None else v.lower()


class CustomerCreate(_CustomerFields):
    business_name: str = Field(min_length=1, max_length=200)
    owner_name: str = Field(min_length=1, max_length=120)
    tax_id: str = Field(min_length=1, max_length=20)
    address_line1: str = Field(min_length=1, max_length=200)
    address_line2: str | None = Field(default=None, max_length=200)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(default="MA", min_length=1, max_length=20)
    postal_code: str = Field(min_length=1, max_length=10)
    phone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    notes: str | None = Field(default=None, max_length=2000)


class CustomerUpdate(_CustomerFields):
    business_name: str | None = Field(default=None, min_length=1, max_length=200)
    owner_name: str | None = Field(default=None, min_length=1, max_length=120)
    tax_id: str | None = Field(default=None, min_length=1, max_length=20)
    address_line1: str | None = Field(default=None, min_length=1, max_length=200)
    address_line2: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    state: str | None = Field(default=None, min_length=1, max_length=20)
    postal_code: str | None = Field(default=None, min_length=1, max_length=10)
    phone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    notes: str | None = Field(default=None, max_length=2000)
    status: CustomerStatus | None = None


class CustomerListItem(BaseModel):
    """One search result row."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    account_number: str
    business_name: str
    owner_name: str
    tax_id_masked: str
    city: str
    state: str
    phone: str | None
    status: CustomerStatus


class CustomerOut(CustomerListItem):
    """Full detail. Still masked: there is deliberately no field for the full tax ID."""

    address_line1: str
    address_line2: str | None
    postal_code: str
    email: str | None
    notes: str | None
    registered_by_user_id: int | None
    created_at: datetime
    updated_at: datetime


class CustomerPage(BaseModel):
    items: list[CustomerListItem]
    total: int
    limit: int
    offset: int


class TaxIdReveal(BaseModel):
    customer_id: int
    account_number: str
    tax_id: str
