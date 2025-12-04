from pydantic import BaseModel, conint, condecimal
from typing import List
from decimal import Decimal


class CartItemBase(BaseModel):
    product_id: int
    quantity: conint(ge=1)


class CartItemCreate(CartItemBase):
    pass


class CartItemUpdate(BaseModel):
    quantity: conint(ge=1)


class CartItemResponse(BaseModel):
    product_id: int
    name: str
    quantity: int
    unit_price: condecimal(max_digits=10, decimal_places=2)
    line_total: condecimal(max_digits=10, decimal_places=2)

    class Config:
        from_attributes = True


class CartOut(BaseModel):
    items: List[CartItemResponse]
    total_items: int
    subtotal: condecimal(max_digits=10, decimal_places=2)

    class Config:
        from_attributes = True
