"""Business logic for staff accounts and authentication."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.modules.audit import service as audit
from app.modules.identity.models import User
from app.modules.identity.schemas import UserCreate, UserUpdate


class EmailAlreadyExists(Exception):
    pass


class CannotRemoveLastAdmin(Exception):
    pass


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def authenticate(db: Session, email: str, password: str) -> User | None:
    """Return the user if the credentials are valid and the account is active."""
    user = get_by_email(db, email)
    if user is None:
        # Hash anyway so response time doesn't reveal whether the email exists.
        verify_password(password, _DUMMY_HASH)
        return None
    if not verify_password(password, user.password_hash) or not user.is_active:
        return None
    user.last_login_at = datetime.now(UTC)
    db.commit()
    return user


def create_user(db: Session, data: UserCreate, actor_id: int | None) -> User:
    if get_by_email(db, data.email):
        raise EmailAlreadyExists(data.email)
    user = User(
        email=data.email.lower(),
        full_name=data.full_name.strip(),
        password_hash=hash_password(data.password),
        role=data.role.value,
    )
    db.add(user)
    db.flush()
    audit.record(
        db,
        action="user.created",
        entity_type="user",
        entity_id=user.id,
        actor_user_id=actor_id,
        details={"email": user.email, "role": user.role},
    )
    db.commit()
    return user


def update_user(db: Session, user: User, data: UserUpdate, actor_id: int) -> User:
    changes: dict = {}
    if data.full_name is not None:
        user.full_name = data.full_name.strip()
        changes["full_name"] = user.full_name
    removing_admin = user.role == "admin" and (
        (data.role is not None and data.role.value != "admin") or data.is_active is False
    )
    if removing_admin and _active_admin_count(db) <= 1:
        raise CannotRemoveLastAdmin()
    if data.role is not None:
        user.role = data.role.value
        changes["role"] = user.role
    if data.is_active is not None:
        user.is_active = data.is_active
        changes["is_active"] = user.is_active
    if data.password is not None:
        user.password_hash = hash_password(data.password)
        changes["password"] = "changed"  # never log the value
    audit.record(
        db,
        action="user.updated",
        entity_type="user",
        entity_id=user.id,
        actor_user_id=actor_id,
        details=changes,
    )
    db.commit()
    return user


def _active_admin_count(db: Session) -> int:
    return len(db.scalars(select(User.id).where(User.role == "admin", User.is_active)).all())


_DUMMY_HASH = hash_password("timing-equaliser-not-a-real-password")
