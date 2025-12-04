import os
import httpx
from fastapi import HTTPException

STOCK_API_URL = os.getenv("STOCK_API_URL", "https://api.cubells.com.ar/stock")
KEYCLOAK_TOKEN_URL = os.getenv("KEYCLOAK_TOKEN_URL", "https://keycloak.cubells.com.ar/realms/ds-2025-realm/protocol/openid-connect/token")
# Dedicated credentials for Stock API
STOCK_CLIENT_ID = os.getenv("STOCK_CLIENT_ID", "grupo-08")
STOCK_CLIENT_SECRET = os.getenv("STOCK_CLIENT_SECRET", "248f42b5-7007-47d1-a94e-e8941f352f6f")


def _get_keycloak_token() -> str:
    """Get Keycloak access token for Stock API"""
    try:
        with httpx.Client() as client:
            resp = client.post(
                KEYCLOAK_TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": STOCK_CLIENT_ID,
                    "client_secret": STOCK_CLIENT_SECRET,
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["access_token"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obtaining Keycloak token for Stock: {str(e)}")


def _map_stock_product_to_front(p: dict) -> dict:
    """Convierte el JSON de stock al formato que espera Producto + tu frontend"""
    # categoría: tomo el nombre de la primera categoría si existe
    category_name = None
    categorias = p.get("categorias") or []
    if categorias:
        category_name = categorias[0].get("nombre")

    # imagen principal
    imagenes = p.get("imagenes") or []
    main_image_url = None
    if imagenes:
        principal = next((img for img in imagenes if img.get("esPrincipal")), imagenes[0])
        main_image_url = principal.get("url")

    return {
        "id": p["id"],
        "name": p.get("nombre", ""),
        "description": p.get("descripcion", ""),
        "price": float(p.get("precio", 0) or 0),
        "sku": str(p["id"]),
        "category": category_name,
        "stock": p.get("stockDisponible", 0),
        "main_image_url": main_image_url,
        "images": [
            {
                "url": img.get("url", ""),
                "is_primary": img.get("esPrincipal", False),
            }
            for img in imagenes
        ],
    }


def listar_productos(page: int = 1, limit: int = 20, q: str | None = None, categoria_id: int | None = None):
    params: dict = {
        "page": page,
        "limit": limit,
    }
    if q:
        params["q"] = q
    if categoria_id:
        params["categoriaId"] = categoria_id

    token = _get_keycloak_token()
    headers = {"Authorization": f"Bearer {token}"}

    try:
        r = httpx.get(f"{STOCK_API_URL}/productos", params=params, headers=headers, timeout=10.0)
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Error al consultar stock: {e.response.text}",
        )
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"No se pudo conectar al servicio de stock: {e}")

    data = r.json()

    # si el endpoint devuelve una lista simple:
    if isinstance(data, list):
        return [_map_stock_product_to_front(p) for p in data]

    # si devuelve algo del estilo {"data": [...]} o {"items": [...]}
    items = data.get("data", data.get("items", []))
    return [_map_stock_product_to_front(p) for p in items]


def obtener_producto(producto_id: int):
    token = _get_keycloak_token()
    headers = {"Authorization": f"Bearer {token}"}

    try:
        r = httpx.get(f"{STOCK_API_URL}/productos/{producto_id}", headers=headers, timeout=10.0)
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Error al consultar stock: {e.response.text}",
        )
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"No se pudo conectar al servicio de stock: {e}")

    data = r.json()
    return _map_stock_product_to_front(data)


def crear_reserva(id_compra: str, usuario_id: int, productos: list[dict]):
    """
    Crea una reserva en la API de Stock.
    Payload esperado por Stock API:
    {
      "idCompra": "string",  # <- STRING
      "usuarioId": 0,         # <- INTEGER
      "productos": [
        {
          "idProducto": 0,
          "cantidad": 0
        }
      ]
    }
    """
    token = _get_keycloak_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "idCompra": id_compra,  # String
        "usuarioId": usuario_id,  # Integer
        "productos": productos
    }

    try:
        r = httpx.post(f"{STOCK_API_URL}/reservas", json=payload, headers=headers, timeout=10.0)
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Error al crear reserva en Stock: {e.response.text}",
        )
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"No se pudo conectar al servicio de stock: {e}")

    return r.json()


def cancelar_reserva(reserva_id: int, motivo: str):
    """
    Cancela una reserva en la API de Stock.
    """
    token = _get_keycloak_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "motivo": motivo
    }

    try:
        # Asumiendo endpoint POST /reservas/{id}/cancelar o similar. 
        # Si es DELETE, ajustar. Según docs previos era POST con motivo.
        r = httpx.post(f"{STOCK_API_URL}/reservas/{reserva_id}/cancelar", json=payload, headers=headers, timeout=10.0)
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        # Si ya estaba cancelada o no existe, a veces devuelven 404 o 400.
        # Podemos loguear y seguir, o relanzar.
        print(f"Warning: Error cancelando reserva {reserva_id}: {e.response.text}")
        # No lanzamos excepción para no romper el rollback de la orden local
        return {"status": "error", "detail": e.response.text}
    except httpx.RequestError as e:
        print(f"Warning: Error conexión cancelando reserva {reserva_id}: {e}")
        return {"status": "error", "detail": str(e)}

    return r.json()
