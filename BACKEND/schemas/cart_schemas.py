# En backend/schemas/cart_schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Molde para un item individual dentro del carrito
class CartItem(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0) # gt=0 asegura que la cantidad sea siempre mayor a cero
    price: float
    name: str
    image_url: Optional[str] = None # Para mostrarlo fácil en el front

# Molde para el objeto principal del carrito
class Cart(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: Optional[str] = None # El ID del usuario si está logueado
    guest_session_id: Optional[str] = None # El ID del invitado si no está logueado
    items: List[CartItem] = []
    last_updated: datetime = Field(default_factory=datetime.now)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }