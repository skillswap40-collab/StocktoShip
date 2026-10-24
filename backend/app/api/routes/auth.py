"""Login and current-user endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.modules.identity import service
from app.modules.identity.models import User
from app.modules.identity.schemas import LoginRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = service.authenticate(db, body.email, body.password)
    if user is None:
        # Same message for unknown email, wrong password, or inactive account.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    minutes = get_settings().access_token_minutes
    return TokenResponse(
        access_token=create_access_token(user.id, user.role, minutes), expires_in=minutes * 60
    )


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
