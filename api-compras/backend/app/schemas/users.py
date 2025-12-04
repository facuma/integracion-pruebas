from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class UserOut(BaseModel):
    id: int
    keycloak_sub: str
    nombre: str
    email: Optional[EmailStr] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    # lo mínimo si querés permitir POST manual
    nombre: str
    email: Optional[EmailStr] = None


# Para enviar a stock / o consulta desde Stock
class CompraItemOut(BaseModel):
    idProducto: int
    nombre: str
    cantidad: int
    precioUnitario: float

class CompraOut(BaseModel):
    idCompra: str
    total: float
    fechaCreacion: datetime
    items: List[CompraItemOut]

class UsuarioComprasOut(BaseModel):
    id: int
    nombre: str
    compras: List[CompraOut]





    