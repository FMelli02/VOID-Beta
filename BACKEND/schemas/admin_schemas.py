# En backend/schemas/admin_schemas.py
from pydantic import BaseModel
from datetime import date, datetime
from typing import List, Optional

class GastoBase(BaseModel):
    descripcion: str
    monto: float
    categoria: str | None = None
    fecha: date

class GastoCreate(GastoBase):
    pass

class Gasto(GastoBase):
    id: int

    class Config:
        from_attributes = True

class ProductSale(BaseModel):
    product_id: int
    cantidad: int

class ManualSaleCreate(BaseModel):
    user_id: Optional[str] = None
    total: float
    productos: List[ProductSale]

class OrdenOut(BaseModel):
    id: int
    user_id: Optional[str]
    total: float
    creado_en: datetime
    productos: List[ProductSale]

    class Config:
        from_attributes = True
