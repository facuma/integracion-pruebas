# app/crud/cart.py
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from decimal import Decimal

from app.models.carts import Cart, CartItem
from app.models.products import Producto as Product


def _build_cart_response(cart: Cart) -> dict:
    """Build CartOut response with calculated fields"""
    items_response = []
    subtotal = Decimal("0.00")
    
    for item in cart.items:
        # Get product info from Stock API
        from app.clients.stock_client import obtener_producto
        try:
            product = obtener_producto(item.product_id)
            unit_price = Decimal(str(product.get('price', 0)))
            line_total = unit_price * item.quantity
            
            items_response.append({
                "product_id": item.product_id,
                "name": product.get('name', f'Product {item.product_id}'),
                "quantity": item.quantity,
                "unit_price": unit_price,
                "line_total": line_total
            })
            subtotal += line_total
        except:
            # If product not found in stock, skip it
            continue
    
    return {
        "items": items_response,
        "total_items": sum(item.quantity for item in cart.items),
        "subtotal": subtotal
    }


def get_or_create_cart(db: Session, user_id: str) -> Cart:
    cart = (
        db.query(Cart)
        .options(joinedload(Cart.items))
        .filter(Cart.user_id == user_id)
        .first()
    )
    if cart is None:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def list_cart_items(db: Session, user_id: str) -> dict:
    cart = (
        db.query(Cart)
        .options(joinedload(Cart.items))
        .filter(Cart.user_id == user_id)
        .first()
    )
    if not cart:
        # Return empty cart
        return {
            "items": [],
            "total_items": 0,
            "subtotal": Decimal("0.00")
        }
    return _build_cart_response(cart)


def add_item_to_cart(db: Session, user_id: str, product_id: int, quantity: int) -> dict:
    """
    Agrega un producto al carrito verificando disponibilidad en Stock API
    """
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Cantidad debe ser mayor a cero")

    # 1. Verificar disponibilidad en Stock API
    from app.clients.stock_client import obtener_producto
    
    try:
        stock_product = obtener_producto(product_id)
    except HTTPException as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Producto no encontrado en Stock")
        raise
    
    # 2. Verificar stock disponible
    if stock_product.get('stock', 0) < quantity:
        raise HTTPException(
            status_code=409,
            detail=f"Stock insuficiente. Disponible: {stock_product.get('stock', 0)}, solicitado: {quantity}"
        )
    
    # 3. Obtener o crear carrito
    cart = get_or_create_cart(db, user_id=user_id)
    
    # 4. Buscar si ya existe item para ese producto
    existing_item = None
    for item in cart.items:
        if item.product_id == product_id:
            existing_item = item
            break

    if existing_item:
        # Verificar que la nueva cantidad total no exceda el stock
        new_total = existing_item.quantity + quantity
        if stock_product.get('stock', 0) < new_total:
            raise HTTPException(
                status_code=409,
                detail=f"Stock insuficiente. Disponible: {stock_product.get('stock', 0)}, en carrito: {existing_item.quantity}, solicitado: {quantity}"
            )
        existing_item.quantity = new_total
    else:
        # Crear nuevo item en carrito
        new_item = CartItem(
            cart_id=cart.id,
            product_id=product_id,
            quantity=quantity,
        )
        db.add(new_item)

    db.commit()
    db.refresh(cart)
    return _build_cart_response(cart)


def update_item_quantity(db: Session, user_id: str, product_id: int, quantity: int) -> dict:
    cart = get_or_create_cart(db, user_id=user_id)

    item = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado en el carrito")

    if quantity <= 0:
        db.delete(item)
    else:
        item.quantity = quantity

    db.commit()
    db.refresh(cart)
    return _build_cart_response(cart)


def clear_cart(db: Session, user_id: str) -> None:
    cart = (
        db.query(Cart)
        .options(joinedload(Cart.items))
        .filter(Cart.user_id == user_id)
        .first()
    )
    if cart:
        for item in list(cart.items):
            db.delete(item)
        db.commit()
