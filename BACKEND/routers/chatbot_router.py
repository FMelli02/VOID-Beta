from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from schemas import chatbot_schemas
from services import ia_services as ia_service
from database.database import get_db
from database.models import ConversacionIA

router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])

# --- CONFIGURACIÓN DE LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/query", response_model=chatbot_schemas.ChatResponse)
async def handle_chat_query(query: chatbot_schemas.ChatQuery, db: AsyncSession = Depends(get_db)):
    """
    Gestiona una consulta del usuario al chatbot, se comunica con la IA
    y guarda el historial de la conversación.
    """
    try:
        # 1. Buscar el historial previo de esta sesión en nuestra DB SQL
        result = await db.execute(
            select(ConversacionIA)
            .filter(ConversacionIA.sesion_id == query.sesion_id)
            .order_by(ConversacionIA.creado_en)
        )
        db_history = result.scalars().all()

        # 2. Guardamos la pregunta actual del usuario en la DB ANTES de llamar a la IA.
        #    Esto es una buena práctica para no perder el prompt del usuario si la IA falla.
        nueva_conversacion = ConversacionIA(
            sesion_id=query.sesion_id,
            prompt=query.pregunta,
            respuesta=""  # La respuesta queda vacía por ahora
        )
        db.add(nueva_conversacion)
        await db.commit()
        await db.refresh(nueva_conversacion)
        
        # Añadimos la pregunta actual al historial que usaremos para la consulta
        # No es necesario añadirla a db_history para build_gemini_history, ya que la nueva pregunta
        # se pasa por separado a get_gemini_response.

        # 3. Obtenemos el catálogo de productos y el prompt del sistema
        dynamic_catalog = await ia_service.get_catalog_from_db(db)
        system_prompt = ia_service.get_chatbot_system_prompt()
        full_system_prompt = f"{system_prompt}\n\n{dynamic_catalog}"

        # 4. Construimos el historial en el formato que le gusta a Gemini
        gemini_history = ia_service.build_gemini_history(db_history)

        # 5. Obtenemos la respuesta de Gemini, enviando solo la pregunta nueva
        respuesta_ia = ia_service.get_gemini_response(full_system_prompt, gemini_history, query.pregunta)

        # 6. Ahora que tenemos la respuesta, actualizamos nuestra DB
        nueva_conversacion.respuesta = respuesta_ia
        db.add(nueva_conversacion)
        await db.commit()

        return chatbot_schemas.ChatResponse(respuesta=respuesta_ia)

    except Exception as e:
        logger.error(f"Error inesperado en el endpoint del chatbot: {e}")
        raise HTTPException(status_code=500, detail="Ocurrió un error interno en el chatbot.")
