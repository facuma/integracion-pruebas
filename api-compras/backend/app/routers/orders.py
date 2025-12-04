from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.crud.order import (
    checkout_from_cart_with_shipping,
    list_user_orders,
    get_user_order,
    cancel_user_order,
)
from app.schemas.orders import OrderOut, OrderListItem
from app.schemas.shipping import CheckoutWithShippingIn
from app.core.keycloak_security import require_auth, require_scope

router = APIRouter(
    prefix="/api/cart",
    tags=["Frontend - Pedidos"],
)


@router.post(
    "/checkout",
    response_model=OrderOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_scope("compras:write"))],
)
def checkout_cart_with_shipping(
    payload: CheckoutWithShippingIn,
    db: Session = Depends(get_db),
    token_data: dict = Depends(require_auth),
):
    user_id = token_data["sub"]
    order = checkout_from_cart_with_shipping(
        db=db,
        user_id=user_id,
        delivery_address=payload.delivery_address,
        transport_type=payload.transport_type,
    )
    return order


@router.get(
    "/history",
    response_model=List[OrderListItem],
    dependencies=[Depends(require_scope("compras:read"))],
)
def history(
    db: Session = Depends(get_db),
    token_data: dict = Depends(require_auth),
):
    user_id = token_data["sub"]
    orders = list_user_orders(db, user_id=user_id)
    return orders


@router.get(
    "/history/{id}",
    response_model=OrderOut,
    dependencies=[Depends(require_scope("compras:read"))],
)
def get_order(
    id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(require_auth),
):
    user_id = token_data["sub"]
    return get_user_order(db, user_id=user_id, order_id=id)


@router.delete(
    "/history/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_scope("compras:write"))],
)
def cancel_order(
    id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(require_auth),
):
    user_id = token_data["sub"]
    cancel_user_order(db, user_id=user_id, order_id=id)
    return


    