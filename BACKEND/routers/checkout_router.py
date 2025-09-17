# En backend/routers/checkout_router.py

import mercadopago
import os
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from schemas import cart_schemas
from database.database import get_db
from database.models import Orden, OrdenProducto
from services import email_service

router = APIRouter(prefix="/api/checkout", tags=["Checkout"])

# --- CONFIGURACIÓN DE LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configura el SDK de Mercado Pago
sdk = mercadopago.SDK(os.getenv("MERCADOPAGO_TOKEN"))

# --- URLs de la aplicación (para desarrollo y producción) ---
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

@router.post("/create_preference")
async def create_preference(cart: cart_schemas.Cart):
    """
    Crea una preferencia de pago en Mercado Pago a partir de un carrito.
    """
    items = []
    for item in cart.items:
        items.append({
            "title": item.name,
            "quantity": item.quantity,
            "unit_price": item.price,
            "currency_id": "ARS"
        })

    preference_data = {
        "items": items,
        "back_urls": {
            "success": f"{FRONTEND_URL}/payment/success",
            "failure": f"{FRONTEND_URL}/payment/failure",
            "pending": f"{FRONTEND_URL}/payment/pending"
        },
        "auto_return": "approved",
        "notification_url": f"{BACKEND_URL}/api/checkout/webhook",
        "external_reference": cart.user_id or cart.guest_session_id # Guardamos el ID del usuario o invitado
    }

    try:
        preference_response = sdk.preference().create(preference_data)
        
        if "response" not in preference_response:
            logger.error(f"Error: La respuesta de Mercado Pago no contiene la clave 'response'. Respuesta completa: {preference_response}")
            raise HTTPException(status_code=500, detail="Error al procesar el pago: Respuesta inesperada de Mercado Pago.")
            
        preference = preference_response["response"]
        
        if "id" not in preference or "init_point" not in preference:
            logger.error(f"Error: La preferencia de Mercado Pago no contiene 'id' o 'init_point'. Preferencia completa: {preference}")
            raise HTTPException(status_code=500, detail="Error al procesar el pago: Datos de preferencia incompletos.")
            
        return {"preference_id": preference["id"], "init_point": preference["init_point"]}
    except KeyError as e:
        logger.error(f"Error de clave al crear la preferencia de Mercado Pago: {e}. Asegúrate de que la respuesta de MP contenga las claves esperadas.")
        raise HTTPException(status_code=500, detail=f"Error al procesar el pago: Falta información clave ({e}).")
    except Exception as e:
        logger.error(f"Error inesperado al crear la preferencia de Mercado Pago: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor al procesar el pago.")

@router.post("/webhook")
async def mercadopago_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Endpoint que recibe las notificaciones de pago de Mercado Pago.
    """
    data = await request.json()
    
    if data.get("type") == "payment":
        payment_id = data.get("data", {}).get("id")
        if not payment_id:
            return {"status": "ignored", "reason": "No payment ID"}

        try:
            payment_info_response = sdk.payment().get(payment_id)
            payment_info = payment_info_response["response"]

            if payment_info["status"] == "approved":
                logger.info(f"Pago aprobado! ID: {payment_id}")
                
                # Guardar la orden en la base de datos
                await save_order_to_db(payment_info, db)
                
                # Enviar email de confirmación
                await email_service.send_order_confirmation_email(payment_info)

        except Exception as e:
            logger.error(f"Error al procesar el webhook de Mercado Pago: {e}")
            # Aún si hay un error, devolvemos un 200 para que MP no siga reintentando.
            return {"status": "error", "detail": str(e)}

    return {"status": "ok"}

async def save_order_to_db(payment_info: dict, db: AsyncSession):
    """
    Guarda la información de la orden en la base de datos.
    """
    user_id = payment_info.get("external_reference")
    total = payment_info.get("transaction_amount")
    
    new_order = Orden(user_id=user_id, total=total)
    db.add(new_order)
    await db.flush()

    for item in payment_info.get("additional_info", {}).get("items", []):
        # NOTA: Mercado Pago no nos devuelve el ID de nuestro producto.
        # Aquí tendríamos que buscar el producto por SKU o nombre si quisiéramos el ID.
        # Por simplicidad, aquí no lo hacemos, pero en un caso real sería necesario.
        order_product = OrdenProducto(
            orden_id=new_order.id,
            # producto_id= ... buscar el id del producto ...
            cantidad=int(item.get("quantity"))
        )
        db.add(order_product)

    await db.commit()
    logger.info(f"Orden {new_order.id} guardada en la base de datos.")
