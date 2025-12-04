from sqlalchemy.orm import Session, joinedload 
from fastapi import HTTPException, status
from decimal import Decimal
import random

from app.models.orders import Order, OrderItem, OrderStatus
from app.models.carts import Cart, CartItem
from app.crud import shipping_client
from app.schemas.shipping import AddressIn


def checkout_from_cart_with_shipping(
    db: Session,
    user_id: str,
    delivery_address: dict,
    transport_type: str,
) -> Order:
    """
    Checkout completo con integración Stock + Logística.
    
    Pasos:
    1. Obtener carrito
    2. Verificar stock en Stock API
    3. Crear reserva en Stock API
    4. Crear orden local
    5. Crear envío en Logística API
    6. Vaciar carrito
    """
    from app.clients.stock_client import obtener_producto, crear_reserva, cancelar_reserva
    
    reservation_id = None
    
    try:
        # ========================================
        # PASO 1: Obtener carrito
        # ========================================
        cart: Cart | None = (
            db.query(Cart)
            .options(joinedload(Cart.items))
            .filter(Cart.user_id == user_id)
            .first()
        )
        
        if not cart or len(cart.items) == 0:
            raise HTTPException(
                status_code=400,
                detail="El carrito está vacío"
            )
        
        print(f"[CHECKOUT] Carrito encontrado con {len(cart.items)} items")
        
        # ========================================
        # PASO 2: Verificar stock y obtener precios
        # ========================================
        total = Decimal("0.00")
        productos_reserva = []
        product_details = {}
        
        for item in cart.items:
            print(f"[CHECKOUT] Verificando producto {item.product_id}")
            
            try:
                stock_product = obtener_producto(item.product_id)
            except Exception as e:
                raise HTTPException(
                    status_code=409,
                    detail=f"Producto {item.product_id} no disponible en Stock"
                )
            
            # Verificar stock suficiente
            if stock_product.get('stock', 0) < item.quantity:
                raise HTTPException(
                    status_code=409,
                    detail=f"Stock insuficiente para {stock_product.get('name')}. "
                           f"Disponible: {stock_product.get('stock', 0)}, "
                           f"Solicitado: {item.quantity}"
                )
            
            # Calcular precio
            price = Decimal(str(stock_product.get('price', 0)))
            total += price * item.quantity
            
            # Guardar para reserva
            product_details[item.product_id] = stock_product
            productos_reserva.append({
                "idProducto": item.product_id,
                "cantidad": item.quantity
            })
        
        print(f"[CHECKOUT] Total calculado: ${total}")
        
        # ========================================
        # PASO 3: Crear reserva en Stock API
        # ========================================
        id_compra_str = f"ORDER-{random.randint(10000, 99999)}"
        
        # Convertir user_id a integer para Stock API
        # Si user_id es "test-user-123", tomamos 123
        try:
            if '-' in user_id:
                usuario_id_int = int(user_id.split('-')[-1])
            else:
                usuario_id_int = abs(hash(user_id)) % 100000
        except:
            usuario_id_int = abs(hash(user_id)) % 100000
        
        print(f"[CHECKOUT] Creando reserva: id_compra={id_compra_str}, usuario_id={usuario_id_int}")
        
        reserva_resp = crear_reserva(
            id_compra=id_compra_str,
            usuario_id=usuario_id_int,
            productos=productos_reserva
        )
        reservation_id = reserva_resp.get('idReserva') or reserva_resp.get('id')
        
        print(f"[CHECKOUT] Reserva creada: ID {reservation_id}")
        
        # ========================================
        # PASO 4: Crear orden local
        # ========================================
        order = Order(
            user_id=user_id,
            status=OrderStatus.PENDING,
            total_amount=total,
            reservation_id=reservation_id
        )
        db.add(order)
        db.flush()  # Para obtener order.id
        
        print(f"[CHECKOUT] Orden creada: ID {order.id}")
        
        # Crear order items
        for item in cart.items:
            stock_product = product_details[item.product_id]
            db.add(
                OrderItem(
                    order_id=order.id,
                    product_id=item.product_id,
                    product_name=stock_product.get('name', 'Producto'),
                    unit_price=Decimal(str(stock_product.get('price', 0))),
                    quantity=item.quantity,
                )
            )
        
        # ========================================
        # PASO 5: Crear envío en Logística API
        # ========================================
        # Logística API expects: {"id": product_id, "quantity": qty}
        products_for_shipping = [
            {"id": item.product_id, "quantity": item.quantity}
            for item in cart.items
        ]
        
        print(f"[CHECKOUT] Products for shipping: {products_for_shipping}")
        print(f"[CHECKOUT] Creando envío para orden {order.id}")
        
        try:
            shipping_resp = shipping_client.crear_envio(
                order_id=order.id,
                user_id=user_id,
                delivery_address=delivery_address,
                transport_type=transport_type,
                products=products_for_shipping,
            )
        except HTTPException as ship_error:
            print(f"[CHECKOUT ERROR] Error creating shipping: {ship_error.status_code} - {ship_error.detail}")
            raise HTTPException(
                status_code=ship_error.status_code,
                detail=f"Error al crear envío: {ship_error.detail}"
            )
        
        order.shipping_id = shipping_resp.get("shipping_id") or shipping_resp.get("id")
        order.shipping_status = shipping_resp.get("status", "pending")
        order.shipping_transport_type = transport_type
        
        print(f"[CHECKOUT] Envío creado: ID {order.shipping_id}")
        
        # ========================================
        # PASO 6: Vaciar carrito
        # ========================================
        for item in list(cart.items):
            db.delete(item)
        
        # ========================================
        # COMMIT FINAL
        # ========================================
        db.commit()
        db.refresh(order)
        
        print(f"[CHECKOUT] Checkout completado exitosamente")
        return order
        
    except HTTPException:
        # Error conocido - rollback y cancelar reserva
        print(f"[CHECKOUT ERROR] HTTPException, haciendo rollback")
        db.rollback()
        if reservation_id:
            try:
                print(f"[CHECKOUT] Cancelando reserva {reservation_id}")
                cancelar_reserva(reservation_id, "Error en checkout")
            except:
                pass
        raise
        
    except Exception as e:
        # Error inesperado - rollback y cancelar reserva
        print(f"[CHECKOUT ERROR] Exception: {str(e)}")
        db.rollback()
        if reservation_id:
            try:
                print(f"[CHECKOUT] Cancelando reserva {reservation_id}")
                cancelar_reserva(reservation_id, "Error en checkout")
            except:
                pass
        raise HTTPException(
            status_code=500,
            detail=f"Error en checkout: {str(e)}"
        )


def list_user_orders(db: Session, user_id: str):
    """Listar órdenes del usuario"""
    return (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .all()
    )


def get_user_order(db: Session, user_id: str, order_id: int) -> Order:
    """Obtener una orden específica"""
    order = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id == order_id, Order.user_id == user_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    return order


def cancel_user_order(db: Session, user_id: str, order_id: int) -> None:
    """
    Cancelar una orden y revertir reserva + envío
    """
    from app.clients.stock_client import cancelar_reserva
    
    order: Order | None = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == user_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden cancelar órdenes en estado PENDING",
        )
    
    # Cancelar reserva en Stock
    if order.reservation_id:
        try:
            print(f"[CANCEL] Cancelando reserva {order.reservation_id}")
            cancelar_reserva(order.reservation_id, "Cancelación por usuario")
        except Exception as e:
            print(f"Error al cancelar reserva: {str(e)}")
    
    # Cancelar envío en Logística
    if order.shipping_id:
        try:
            print(f"[CANCEL] Cancelando envío {order.shipping_id}")
            shipping_client.cancelar_envio(order.shipping_id)
        except Exception as e:
            print(f"Error al cancelar envío: {str(e)}")

    order.status = OrderStatus.CANCELED
    order.shipping_status = "cancelled"
    db.commit()
    
    print(f"[CANCEL] Orden {order_id} cancelada")
