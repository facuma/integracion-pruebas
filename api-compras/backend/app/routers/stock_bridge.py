#Endpoint para que Stock consulte usuario + compras

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.db import get_db
from app.core.keycloak_security import require_scope, require_auth
from app.models.users import User
from app.models.orders import Order
from app.schemas.users import UsuarioComprasOut, CompraOut, CompraItemOut

router = APIRouter(
    prefix="/api/stock",
    tags=["Compras ↔ Stock"],
)

@router.get(
    "/usuarios/{usuario_id}/compras",
    response_model=UsuarioComprasOut,
    dependencies=[Depends(require_scope("compras:read"))],
)
def compras_por_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    token: dict = Depends(require_auth),
):
    user = db.query(User).filter(User.id == usuario_id).first()
    if not user:
        raise HTTPException(404, "Usuario no encontrado")

    orders = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.user_id == user.keycloak_sub)
        .all()
    )

    compras = []
    for o in orders:
        compras.append(
            CompraOut(
                idCompra=f"COMPRA-{o.id}",
                total=float(o.total_amount),
                fechaCreacion=o.created_at,
                items=[
                    CompraItemOut(
                        idProducto=i.product_id,
                        nombre=i.product_name,
                        cantidad=i.quantity,
                        precioUnitario=float(i.unit_price),
                    )
                    for i in o.items
                ]
            )
        )

    return UsuarioComprasOut(id=user.id, nombre=user.nombre, compras=compras)
