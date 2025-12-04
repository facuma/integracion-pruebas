from pydantic import BaseModel, conint, condecimal
from typing import List
from datetime import datetime
from enum import Enum


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELED = "CANCELED"


class OrderItemBase(BaseModel):
    id: int
    product_id: int
    product_name: str
    unit_price: condecimal(max_digits=10, decimal_places=2)
    quantity: conint(ge=1)

    class Config:
        from_attributes = True


class OrderItemOut(OrderItemBase):
    """
    Representa un ítem de la orden (producto + cantidad + precio).
    Hereda todos los campos de OrderItemBase.
    """
    pass


class OrderOut(BaseModel):
    """
    Orden completa, con ítems + datos de envío.
    """
    id: int
    status: OrderStatus
    total_amount: condecimal(max_digits=10, decimal_places=2)
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemOut]

    # ===== Campos de logística (envío) =====
    shipping_id: int | None = None
    shipping_status: str | None = None
    shipping_transport_type: str | None = None
    shipping_total_cost: condecimal(max_digits=10, decimal_places=2) | None = None
    shipping_currency: str | None = None

    class Config:
        from_attributes = True


class OrderListItem(BaseModel):
    """
    Versión reducida para listados / historial.
    """
    id: int
    status: OrderStatus
    total_amount: condecimal(max_digits=10, decimal_places=2)
    created_at: datetime

    # resumen de envío
    shipping_status: str | None = None
    shipping_transport_type: str | None = None

    class Config:
        from_attributes = True
