# app/routers/auth.py
# Simplified auth - no Keycloak, just local user management

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.users import User

router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
)


class UserCreate(BaseModel):
    user_id: str  # External ID from frontend (email, UUID, etc)
    nombre: str | None = None
    email: EmailStr | None = None


class UserOut(BaseModel):
    id: int
    user_id: str
    nombre: str | None
    email: str | None

    class Config:
        from_attributes = True


@router.post(
    "",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Create a local user record.
    Frontend provides the user_id (whatever their auth system uses).
    """
    # Check if user already exists
    existing = db.query(User).filter(User.user_id == user_data.user_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with user_id='{user_data.user_id}' already exists",
        )
    
    # Create user
    user = User(
        user_id=user_data.user_id,
        nombre=user_data.nombre,
        email=user_data.email,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.get(
    "/{user_id}",
    response_model=UserOut,
)
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
):
    """Get user by their external user_id"""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with user_id='{user_id}' not found",
        )
    return user
