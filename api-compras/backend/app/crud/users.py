from sqlalchemy.orm import Session
from app.models.users import User

def get_user_by_sub(db: Session, sub: str) -> User | None:
    return db.query(User).filter(User.keycloak_sub == sub).first()

def upsert_user_from_token(db: Session, token_payload: dict) -> User:
    sub = token_payload["sub"]

    # claims típicos de Keycloak
    email = token_payload.get("email")
    given = token_payload.get("given_name")
    family = token_payload.get("family_name")
    preferred = token_payload.get("preferred_username")

    nombre = " ".join([x for x in [given, family] if x]) or preferred or email or sub

    user = get_user_by_sub(db, sub)
    if user:
        user.nombre = nombre
        user.email = email
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    user = User(keycloak_sub=sub, nombre=nombre, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user