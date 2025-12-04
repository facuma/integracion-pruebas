from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.core.keycloak_security import require_auth, require_scope
from app.crud.users import get_user_by_sub, upsert_user_from_token
from app.schemas.users import UserOut, UserCreate

router = APIRouter(
    prefix="/api/users",
    tags=["Frontend - Usuario"],
)

@router.get(
    "/me",
    response_model=UserOut,
    dependencies=[Depends(require_scope("usuarios:read"))],
)
def get_me(
    db: Session = Depends(get_db),
    token: dict = Depends(require_auth),
):
    sub = token["sub"]
    user = get_user_by_sub(db, sub)
    if not user:
        # si no existe, lo creamos con claims
        user = upsert_user_from_token(db, token)
    return user


@router.post(
    "/me",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_scope("usuarios:write"))],
)
def post_me(
    db: Session = Depends(get_db),
    token: dict = Depends(require_auth),
):
    # POST “register/upsert” basado en Keycloak
    user = upsert_user_from_token(db, token)
    return user


# opcional: POST admin/manual (si lo querés)
@router.post(
    "",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_scope("usuarios:write"))],
)
def create_user_manual(
    body: UserCreate,
    db: Session = Depends(get_db),
    token: dict = Depends(require_auth),
):
    # sub del token → usuario dueño
    payload = {**token, "email": body.email, "given_name": body.nombre}
    return upsert_user_from_token(db, payload)
