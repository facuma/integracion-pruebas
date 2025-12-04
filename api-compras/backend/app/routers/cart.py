from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.crud.cart import (
    list_cart_items,
    add_item_to_cart,
    update_item_quantity,
    clear_cart,
)
from app.crud.order import checkout_from_cart_with_shipping

from app.schemas.carts import CartOut, CartItemUpdate, CartItemCreate
from app.schemas.shipping import AddressIn
from app.schemas.orders import OrderOut

from pydantic import BaseModel


router = APIRouter(
    prefix="/api/cart",
    tags=["Frontend - Carrito"],
)


# ====================
# GET CART
# ====================
@router.get(
    "",
    response_model=CartOut,
)
def get_cart(
    user_id: str = Query(..., description="User ID from frontend"),
    db: Session = Depends(get_db),
):
    """Get user's cart. User ID is provided by frontend."""
    cart = list_cart_items(db, user_id=user_id)
    return cart


# ====================
# ADD ITEM
# ====================
@router.post(
    "",
    response_model=CartOut,
    status_code=status.HTTP_201_CREATED,
)
def add_item(
    item: CartItemCreate,
    user_id: str = Query(..., description="User ID from frontend"),
    db: Session = Depends(get_db),
):
    """Add item to cart with Stock API verification. User ID is provided by frontend."""
    cart = add_item_to_cart(
        db,
        user_id=user_id,
        product_id=item.product_id,
        quantity=item.quantity,
    )
    return cart


# ====================
# UPDATE ITEM QUANTITY
# ====================
@router.put(
    "/{product_id}",
    response_model=CartOut,
)
def update_item(
    product_id: int,
    item: CartItemUpdate,
    user_id: str = Query(..., description="User ID from frontend"),
    db: Session = Depends(get_db),
):
    """Update item quantity in cart. User ID is provided by frontend."""
    cart = update_item_quantity(
        db, user_id=user_id, product_id=product_id, quantity=item.quantity
    )
    return cart


# ====================
# CLEAR CART
# ====================
@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
)
def clear_user_cart(
    user_id: str = Query(..., description="User ID from frontend"),
    db: Session = Depends(get_db),
):
    """Clear all items from cart. User ID is provided by frontend."""
    clear_cart(db, user_id=user_id)
    return None


# =============================
# CHECKOUT WITH SHIPPING
# =============================
class CheckoutRequest(BaseModel):
    delivery_address: AddressIn
    transport_type: str  # e.g., "truck", "ship", "air"


@router.post(
    "/checkout",
    response_model=OrderOut,
    status_code=status.HTTP_201_CREATED,
)
def checkout_cart(
    req: CheckoutRequest,
    user_id: str = Query(..., description="User ID from frontend"),
    db: Session = Depends(get_db),
):
    """
    Checkout from cart:
    1. Creates Stock reservation
    2. Creates local order
    3. Creates Logistica shipping
    4. Rollback reservation if shipping fails
    
    User ID is provided by frontend.
    """
    order = checkout_from_cart_with_shipping(
        db,
        user_id=user_id,
        delivery_address=req.delivery_address.dict(),
        transport_type=req.transport_type,
    )
    return order


# =============================
# ORDER HISTORY
# =============================
@router.get(
    "/history",
    response_model=List[OrderOut],
)
def get_order_history(
    user_id: str = Query(..., description="User ID from frontend"),
    db: Session = Depends(get_db),
):
    """Get user's order history. User ID is provided by frontend."""
    from app.crud.order import list_user_orders
    orders = list_user_orders(db, user_id=user_id)
    return orders


@router.get(
    "/history/{order_id}",
    response_model=OrderOut,
)
def get_order_detail(
    order_id: int,
    user_id: str = Query(..., description="User ID from frontend"),
    db: Session = Depends(get_db),
):
    """Get user's order details. User ID is provided by frontend."""
    from app.crud.order import get_user_order
    order = get_user_order(db, user_id=user_id, order_id=order_id)
    return order


@router.delete(
    "/history/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def cancel_order(
    order_id: int,
    user_id: str = Query(..., description="User ID from frontend"),
    db: Session = Depends(get_db),
):
    """Cancel order (cancels Stock reservation and Logistica shipping). User ID is provided by frontend."""
    from app.crud.order import cancel_user_order
    cancel_user_order(db, user_id=user_id, order_id=order_id)
    return None