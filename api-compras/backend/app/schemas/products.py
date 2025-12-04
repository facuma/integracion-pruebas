from typing import Optional, List
from pydantic import BaseModel


class Dimensiones(BaseModel):
    largoCm: Optional[float] = None
    anchoCm: Optional[float] = None
    altoCm: Optional[float] = None


class Categoria(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]


class Imagen(BaseModel):
    url: str
    esPrincipal: bool


class ProductoOut(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    precio: float
    stockDisponible: int
    dimensiones: Optional[Dimensiones]
    categorias: Optional[List[Categoria]]
    imagenes: Optional[List[Imagen]]
