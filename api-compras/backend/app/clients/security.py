# app/security.py
import os
from functools import lru_cache

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel

# URL de tu Keycloak
KEYCLOAK_BASE_URL = os.getenv("KEYCLOAK_BASE_URL", "http://keycloak:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "ds-2025-realm")

ISSUER = f"{KEYCLOAK_BASE_URL}/realms/{KEYCLOAK_REALM}"
JWKS_URL = f"{ISSUER}/protocol/openid-connect/certs"

# Sólo usamos esto para que FastAPI lea el header Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

class KCUser(BaseModel):
    sub: str
    email: str | None = None
    preferred_username: str | None = None
    given_name: str | None = None
    family_name: str | None = None


@lru_cache()
def get_jwks():
    """Descarga y cachea la JWKS de Keycloak (claves públicas RSA)."""
    resp = httpx.get(JWKS_URL, timeout=5.0)
    if resp.status_code != 200:
        print("Error obteniendo JWKS de Keycloak:", resp.status_code, resp.text)
        raise RuntimeError("No se pudo obtener JWKS de Keycloak")
    return resp.json()


def decode_keycloak_token(token: str) -> dict:
    """Verifica la firma del JWT usando la JWKS de Keycloak y devuelve los claims."""
    jwks = get_jwks()

    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cabecera de token inválida",
        )

    kid = unverified_header.get("kid")
    if not kid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sin 'kid' en el header",
        )

    key = next((k for k in jwks["keys"] if k.get("kid") == kid), None)
    if key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se encontró clave para ese 'kid'",
        )

    try:
        # verify_aud lo desactivamos por simplicidad, si querés podés validarlo
        decoded = jwt.decode(
            token,
            key,
            algorithms=[unverified_header.get("alg", "RS256")],
            audience=None,
            issuer=ISSUER,
            options={"verify_aud": False},
        )
        return decoded
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )


async def get_current_user(token: str = Depends(oauth2_scheme)) -> KCUser:
    """Dependencia que devuelve el usuario ya validado a partir del token."""
    decoded = decode_keycloak_token(token)

    user_data = {
        "sub": decoded.get("sub"),
        "email": decoded.get("email"),
        "preferred_username": decoded.get("preferred_username"),
        "given_name": decoded.get("given_name"),
        "family_name": decoded.get("family_name"),
    }

    return KCUser(**user_data)
