# app/core/keycloak_security.py

import os
from functools import lru_cache

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


# === Config de Keycloak ===
KEYCLOAK_BASE_URL = os.getenv("KEYCLOAK_BASE_URL", "http://keycloak:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "ds-2025-realm")

ISSUER = f"{KEYCLOAK_BASE_URL}/realms/{KEYCLOAK_REALM}"
JWKS_URL = f"{ISSUER}/protocol/openid-connect/certs"

# Solo lo usamos para leer el header Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
security = HTTPBearer(auto_error=False)


@lru_cache()
def get_jwks() -> dict:
    """
    Descarga y cachea las claves públicas (JWKS) de Keycloak.
    """
    resp = httpx.get(JWKS_URL, timeout=5.0)
    if resp.status_code != 200:
        print("Error obteniendo JWKS de Keycloak:", resp.status_code, resp.text)
        raise RuntimeError("No se pudo obtener JWKS de Keycloak")
    return resp.json()


def decode_keycloak_token(token: str) -> dict:
    """
    Verifica la firma del JWT usando las claves públicas de Keycloak
    y devuelve los claims decodificados.
    """
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
            detail="No se encontró clave pública para ese 'kid'",
        )

    try:
        decoded = jwt.decode(
            token,
            key,
            algorithms=[unverified_header.get("alg", "RS256")],
            issuer=ISSUER,
            audience=None,
            options={"verify_aud": False},  # si querés validar 'aud', lo podés activar
        )
        return decoded
    except JWTError as e:
        print("Error decodificando token KC:", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )


# === DEPENDENCIAS QUE USA TU ROUTER ===

# === DEPENDENCIAS QUE USA TU ROUTER ===

ENABLE_MOCK_AUTH = os.getenv("ENABLE_MOCK_AUTH", "False").lower() == "true"

async def require_auth(token_str: str = Depends(oauth2_scheme)) -> dict:
    """
    Dependencia que:
      - lee Authorization: Bearer <token>
      - verifica el token contra Keycloak
      - devuelve el payload decodificado (dict)
    """
    if ENABLE_MOCK_AUTH:
        return {
            "sub": "mock-user-uuid",
            "email": "mock@example.com",
            "given_name": "Mock",
            "family_name": "User",
            "scope": "compras:read compras:write envios:read envios:write productos:read"
        }
        
    decoded = decode_keycloak_token(token_str)
    return decoded

# Devuelve el JWT crudo enviado por el frontend
def get_bearer_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    if ENABLE_MOCK_AUTH:
        return "mock-token"
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing credentials")
    return credentials.credentials


def require_scope(required_scope: str):
    """
    Crea una dependencia que verifica que el token tenga un scope dado.

    Se usa así:
      dependencies=[Depends(require_scope("usuarios:read"))]
    """

    async def _check_scope(token: dict = Depends(require_auth)):
        if ENABLE_MOCK_AUTH:
            return # Mock user has all scopes

        # OJO: depende de cómo estés mapeando scopes/roles.
        # Aquí asumo que Keycloak mete los scopes en el claim "scope" separado por espacios.
        scope_str = token.get("scope", "") or ""
        scopes = scope_str.split()

        if required_scope not in scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tenés el scope requerido: {required_scope}",
            )

    return _check_scope
