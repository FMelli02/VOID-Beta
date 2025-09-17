import os
import logging
import google.generativeai as genai
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from dotenv import load_dotenv

from database.models import Producto, ConversacionIA

load_dotenv()

# --- Configuración de logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuración de Gemini ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", 'gemini-1.5-flash')

model = None
if not GEMINI_API_KEY:
    logger.error("¡ERROR FATAL! No se encontró la GEMINI_API_KEY en el archivo .env")
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)
    except Exception as e:
        logger.error(f"Error al configurar el modelo de Gemini: {e}")

# --- Funciones del servicio ---

async def get_catalog_from_db(db: AsyncSession) -> str:
    """
    Obtiene el catálogo de productos desde la base de datos SQL y arma un texto descriptivo.
    """
    try:
        result = await db.execute(select(Producto))
        products = result.scalars().all()
        
        if not products:
            return "No hay productos disponibles en este momento."

        catalog_string = "--- INICIO DEL CATÁLOGO DE PRODUCTOS DISPONIBLES ---\n"
        for prod in products:
            catalog_string += f"- PRODUCTO: {prod.nombre} | PRECIO: ${prod.precio} | DESCRIPCIÓN: {prod.descripcion}\n"
        catalog_string += "--- FIN DEL CATÁLOGO ---"
        return catalog_string
    except Exception as e:
        logger.error(f"Error al obtener el catálogo de la base de datos: {e}")
        return "Error al obtener el catálogo."

def get_chatbot_system_prompt() -> str:
    """
    Define la personalidad y reglas del chatbot.
    """
    return (
        "Eres Jarvis, un asistente de ventas experto para 'VOID', una tienda de indumentaria de lujo, "
        "minimalista y exclusiva. Tu personalidad es amable, canchera y muy eficiente. Tuteá al cliente.\n\n"
        "**REGLAS DE ORO:**\n"
        "1. Respondé ÚNICAMENTE con la información del catálogo que te proveyeron.\n"
        "2. Si no sabés algo, decilo sin inventar. Sé honesto, por ejemplo di \"Disculpá, no tengo esa información\".\n"
        "3. Sé conciso y andá al grano. No uses más de 30 palabras por respuesta.\n"
        "4. Nunca menciones que eres una IA o un modelo de lenguaje.\n"
        "5. Si el cliente te saluda, responde el saludo amablemente y preguntale en qué podés ayudarlo.\n"
    )

def build_gemini_history(db_history: list[ConversacionIA]) -> list[str]:
    """
    Construye el historial de texto concatenado a partir del historial guardado en DB.
    Retorna una lista de strings que serán concatenadas para el prompt.
    """
    history_lines = []
    for entry in db_history:
        if entry.prompt:
            history_lines.append("Usuario: " + entry.prompt.strip())
        if entry.respuesta:
            history_lines.append("Jarvis: " + entry.respuesta.strip())
    return history_lines

def get_gemini_response(system_instruction: str, gemini_history: list[str], new_question: str) -> str:
    if not model:
        return "Disculpá, el servicio de IA no está disponible en este momento."
    
    try:
        # Construir el prompt completo
        prompt_parts = []
        if system_instruction:
            prompt_parts.append(system_instruction)
        
        prompt_parts.extend(gemini_history)
        prompt_parts.append(f"Usuario: {new_question}")
        prompt_parts.append("Jarvis:")
        
        full_prompt = "\n".join(prompt_parts)

        # Enviar el prompt al modelo
        response = model.generate_content(full_prompt)

        return response.text.strip()

    except Exception as e:
        logger.error(f"Error al comunicarse con Gemini: {e}")
        return "Disculpá, estoy teniendo problemas técnicos para responder en este momento."


