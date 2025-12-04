from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from app.schemas.frontend_products import FrontendProduct, FrontendProductImage
from app.models.products import Producto
from app.clients.stock_client import listar_productos, obtener_producto
#from app.core.keycloak_security import require_auth, require_scope

router = APIRouter(
    prefix="/api/products",
    tags=["Frontend - Productos"],
)


def map_stock_product_to_frontend(stock_p: dict) -> FrontendProduct:
    # nombre / descripcion / precio
    name = stock_p.get("nombre", "")
    description = stock_p.get("descripcion")
    price = stock_p.get("precio", 0.0)

    # stockDisponible → stock
    stock = stock_p.get("stockDisponible", 0)

    # categorías → categoría principal
    categorias = stock_p.get("categorias") or []
    category = categorias[0]["nombre"] if categorias else None

    # imágenes
    imagenes = stock_p.get("imagenes") or []
    images: list[FrontendProductImage] = []
    main_image_url = None

    for img in imagenes:
        url = img.get("url")
        is_principal = img.get("esPrincipal", False)

        fe_img = FrontendProductImage(
            url=url,
            is_primary=is_principal,
        )
        images.append(fe_img)

        if is_principal and url:
            main_image_url = url

    if not main_image_url and images:
        main_image_url = images[0].url

    # sku inventado (si no existe en stock)
    sku = f"SKU-{stock_p.get('id')}" if stock_p.get("id") is not None else None

    return FrontendProduct(
        id=stock_p["id"],
        name=name,
        description=description,
        price=price,
        sku=sku,
        category=category,
        stock=stock,
        main_image_url=main_image_url,
        images=images,
    )


@router.get("", response_model=List[Producto])
def list_products(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    q: Optional[str] = None,
    categoriaId: Optional[int] = None,
):
    return listar_productos(page=page, limit=limit, q=q, categoria_id=categoriaId)


@router.get("/{producto_id}", response_model=Producto)
def get_product(producto_id: int):
    return obtener_producto(producto_id)