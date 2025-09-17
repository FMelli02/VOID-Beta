# En backend/schemas/product_schemas.py

from pydantic import BaseModel, Field
from typing import Optional

# Schema base del producto, con los campos comunes
class ProductBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    precio: float
    sku: str
    material: Optional[str] = None
    talle: Optional[str] = None
    color: Optional[str] = None
    stock: int = Field(..., ge=0) # Nuevo campo para el stock
    categoria_id: int

# Schema para crear un producto (todos los campos de ProductBase son requeridos)
class ProductCreate(ProductBase):
    pass

# Schema para actualizar un producto (todos los campos son opcionales)
class ProductUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    precio: Optional[float] = None
    sku: Optional[str] = None
    material: Optional[str] = None
    talle: Optional[str] = None
    color: Optional[str] = None
    stock: Optional[int] = Field(None, ge=0) # Nuevo campo para el stock
    categoria_id: Optional[int] = None

# Schema para mostrar un producto en la base de datos (incluye el id)
class Product(ProductBase):
    id: int

    class Config:
        from_attributes = True # Permite que Pydantic lea los datos desde un objeto de SQLAlchemy