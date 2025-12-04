from typing import Optional, List
from pydantic import BaseModel


class FrontendProductImage(BaseModel):
    url: Optional[str] = None
    is_primary: Optional[bool] = None


class FrontendProduct(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    sku: Optional[str] = None
    category: Optional[str] = None
    stock: int
    main_image_url: Optional[str] = None
    images: Optional[List[FrontendProductImage]] = None
