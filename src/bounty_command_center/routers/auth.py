from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from sqlmodel import Session
from .. import auth, security, user_manager, schemas
from ..database import get_session
from ..config import settings
from ..models import User

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

@router.post("/users", response_model=schemas.UserRead, status_code=201)
def create_user(
    user_in: schemas.UserCreate,
    db: Session = Depends(get_session),
):
    """
    Create a new user.
    """
    um = user_manager.UserManager()
    user = um.get_user_by_username(db=db, username=user_in.username)
    if user:
        raise HTTPException(status_code=400, detail="Username already registered")

    user = um.add_user(db=db, username=user_in.username, password=user_in.password, role=user_in.role)
    return user

@router.post("/token", response_model=auth.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_session),
):
    """
    Provides a JWT token for authenticated users.
    """
    um = user_manager.UserManager()
    user = um.get_user_by_username(db=db, username=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.auth.jwt_expire_minutes)
    access_token = auth.create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}
