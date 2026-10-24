"""Staff account management. Admins manage accounts; managers can view them."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.modules.identity import service
from app.modules.identity.models import Role, User
from app.modules.identity.schemas import UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.ADMIN, Role.MANAGER)),
) -> list[User]:
    return list(db.scalars(select(User).order_by(User.full_name)))


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(Role.ADMIN)),
) -> User:
    try:
        return service.create_user(db, body, actor_id=actor.id)
    except service.EmailAlreadyExists:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Email already in use") from None


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(Role.ADMIN)),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    try:
        return service.update_user(db, user, body, actor_id=actor.id)
    except service.CannotRemoveLastAdmin:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="Cannot remove the last active admin"
        ) from None
