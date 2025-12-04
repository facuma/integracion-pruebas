# app/crud/shipping_client.py
import os
import httpx
from typing import List, Dict, Any, Optional
from fastapi import HTTPException

SHIPPING_API_URL = os.getenv("SHIPPING_API_URL", "http://shipping_back:3010")
KEYCLOAK_TOKEN_URL = os.getenv("KEYCLOAK_TOKEN_URL")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET")

# 👇 Scopes que va a pedir el backend de Compras para hablar con Logística
SHIPPING_SCOPES = os.getenv(
    "SHIPPING_SCOPES",
    "envios:read envios:write productos:read",
)


def _get_shipping_access_token(scope: Optional[str] = None) -> str:
    """
    Saca un access_token de Keycloak usando client_credentials
    (igual que hacemos para hablar con Stock).
    Ese token se usa solo entre COMPRAS y LOGÍSTICA.
    """
    if scope is None:
        scope = SHIPPING_SCOPES

    if not KEYCLOAK_TOKEN_URL or not KEYCLOAK_CLIENT_ID or not KEYCLOAK_CLIENT_SECRET:
        raise RuntimeError("Faltan env de Keycloak para Logística")

    with httpx.Client() as client:
        resp = client.post(
            KEYCLOAK_TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": KEYCLOAK_CLIENT_ID,
                "client_secret": KEYCLOAK_CLIENT_SECRET,
                "scope": scope,
            },
            timeout=10.0,
        )

    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo obtener token para Logística ({resp.text})",
        )

    data = resp.json()
    return data["access_token"]


# =============== TRANSPORT METHODS ===============

def listar_metodos_transporte() -> Dict[str, Any]:
    token = _get_shipping_access_token("envios:read")
    with httpx.Client() as client:
        resp = client.get(
            f"{SHIPPING_API_URL}/shipping/transport-methods",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )

    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Error al obtener métodos de transporte ({resp.text})",
        )

    return resp.json()


# =============== SHIPPING COST (QUOTE) ===============

def cotizar_envio(
    delivery_address: Dict[str, Any],
    products: List[Dict[str, int]],
) -> Dict[str, Any]:
    """
    Llama a POST /shipping/cost de Logística.
    """
    token = _get_shipping_access_token("envios:read productos:read")

    payload = {
        "delivery_address": delivery_address,
        "products": products,
    }

    with httpx.Client() as client:
        resp = client.post(
            f"{SHIPPING_API_URL}/shipping/cost",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )

    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Error al cotizar envío ({resp.text})",
        )

    return resp.json()


# =============== CREATE SHIPPING ===============

def crear_envio(
    order_id: int,
    user_id: int | str,
    delivery_address: Dict[str, Any],
    transport_type: str,
    products: List[Dict[str, int]],
) -> Dict[str, Any]:
    """
    Llama a POST /shipping de Logística para crear el envío real.
    """
    token = _get_shipping_access_token("envios:write productos:read")

    payload = {
        "order_id": order_id,
        "user_id": int(user_id),
        "delivery_address": delivery_address,
        "transport_type": transport_type,
        "products": products,
    }

    with httpx.Client() as client:
        resp = client.post(
            f"{SHIPPING_API_URL}/shipping",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )

    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Error al crear envío ({resp.text})",
        )

    return resp.json()


# =============== DETALLE + CANCELAR (si los usás) ===============

def obtener_envio(shipping_id: int) -> Dict[str, Any]:
    token = _get_shipping_access_token("envios:read")
    with httpx.Client() as client:
        resp = client.get(
            f"{SHIPPING_API_URL}/shipping/{shipping_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )

    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Envío no encontrado en Logística")

    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Error al obtener envío ({resp.text})",
        )

    return resp.json()


def cancelar_envio(shipping_id: int) -> Dict[str, Any]:
    token = _get_shipping_access_token("envios:write")
    with httpx.Client() as client:
        resp = client.post(
            f"{SHIPPING_API_URL}/shipping/{shipping_id}/cancel",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )

    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Envío no encontrado en Logística")

    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Error al cancelar envío ({resp.text})",
        )

    return resp.json()

