from fastapi import APIRouter, Depends, HTTPException, Header
from pymongo.database import Database
from typing import Optional
from datetime import datetime
import uuid

from schemas import cart_schemas
from database.database import get_db_nosql
from utils.security import get_current_user_optional

router = APIRouter(
    prefix="/api/cart",
    tags=["Shopping Cart"]
)

# --- Helper para obtener el ID del que hace el pedido ---
def get_session_identifier(current_user: Optional[dict], guest_id: Optional[str]):
    if current_user:
        return {"user_id": current_user["id"]}
    if guest_id:
        return {"guest_session_id": guest_id}
    raise HTTPException(status_code=400, detail="Se requiere sesión de usuario o de invitado.")

# --- Endpoint para que el frontend pida un ID de invitado ---
@router.get("/session/guest", summary="Generar un ID de sesión para invitados")
def get_guest_session():
    return {"guest_session_id": str(uuid.uuid4())}

# --- Endpoints del Carrito ---

@router.get("/", response_model=cart_schemas.Cart, summary="Obtener el carrito actual")
async def get_cart(
    guest_session_id: Optional[str] = Header(None, alias="X-Guest-Session-ID"),
    db: Database = Depends(get_db_nosql),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    identifier = get_session_identifier(current_user, guest_session_id)
    cart = await db.carts.find_one(identifier)
    
    if not cart:
        new_cart_data = identifier.copy()
        new_cart_data.update({"items": [], "last_updated": datetime.now()})
        return cart_schemas.Cart(**new_cart_data)
        
    return cart_schemas.Cart(**cart)

@router.post("/items", response_model=cart_schemas.Cart, summary="Añadir un item al carrito")
async def add_item_to_cart(
    item: cart_schemas.CartItem,
    guest_session_id: Optional[str] = Header(None, alias="X-Guest-Session-ID"),
    db: Database = Depends(get_db_nosql),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    identifier = get_session_identifier(current_user, guest_session_id)
    
    # Primero, intentamos actualizar la cantidad si el producto ya existe en el carrito
    result = await db.carts.update_one(
        {**identifier, "items.product_id": item.product_id},
        {"$inc": {"items.$.quantity": item.quantity}}
    )

    # Si no se modificó nada, significa que el producto no estaba, así que lo agregamos
    if result.modified_count == 0:
        await db.carts.update_one(
            identifier,
            {
                "$push": {"items": item.model_dump()},
                "$set": {"last_updated": datetime.now()}
            },
            upsert=True  # Crea el carrito si no existe
        )
        
    updated_cart = await db.carts.find_one(identifier)
    return cart_schemas.Cart(**updated_cart)

@router.delete("/items/{product_id}", response_model=cart_schemas.Cart, summary="Eliminar un item del carrito")
async def remove_item_from_cart(
    product_id: int,
    guest_session_id: Optional[str] = Header(None, alias="X-Guest-Session-ID"),
    db: Database = Depends(get_db_nosql),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    identifier = get_session_identifier(current_user, guest_session_id)
    
    await db.carts.update_one(
        identifier,
        {"$pull": {"items": {"product_id": product_id}}}
    )
    
    updated_cart = await db.carts.find_one(identifier)
    return cart_schemas.Cart(**updated_cart)
