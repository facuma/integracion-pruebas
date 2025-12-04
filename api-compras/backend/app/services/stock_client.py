# app/clients/stock_client.py
import os
import httpx

STOCK_API_URL = os.getenv("STOCK_API_URL", "http://stock:8000/v1")
KEYCLOAK_TOKEN_URL = os.getenv("KEYCLOAK_TOKEN_URL")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET")


async def _get_access_token(scope: str = "productos:read") -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            KEYCLOAK_TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": KEYCLOAK_CLIENT_ID,
                "client_secret": KEYCLOAK_CLIENT_SECRET,
                "scope": scope,
            },
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


async def listar_productos(page: int, limit: int, q: str | None, categoria_id: int | None):
    token = await _get_access_token()
    params: dict = {"page": page, "limit": limit}
    if q:
        params["q"] = q
    if categoria_id is not None:
        params["categoriaId"] = categoria_id

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{STOCK_API_URL}/productos",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
        )
        resp.raise_for_status()
        return resp.json()  # lista de dicts


async def obtener_producto(producto_id: int):
    token = await _get_access_token()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{STOCK_API_URL}/productos/{producto_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        return resp.json()  # un dict
