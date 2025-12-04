from pydantic import BaseModel
from typing import List, Optional


class ProductImage(BaseModel):
    url: str
    is_primary: bool = False


class Producto(BaseModel):
    id: int
    name: str                    # viene de "nombre"
    description: str             # viene de "descripcion"
    price: float                 # viene de "precio" (string en stock)
    sku: Optional[str] = None
    category: Optional[str] = None
    stock: int                   # viene de "stockDisponible"
    main_image_url: Optional[str] = None
    images: List[ProductImage] = []
