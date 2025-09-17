import asyncio
import imaplib
import email
import logging
import os
import smtplib
import sys
from email.utils import parseaddr
from dotenv import load_dotenv

# --- Agrego ruta raíz del proyecto para importar módulos ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from services import ia_services
from database.database import AsyncSessionLocal

# --- Configuración ---
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IMAP_SERVER = "imap.gmail.com"
EMAIL_ACCOUNT = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def get_email_body(msg):
    """Extrae cuerpo texto plano del email."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode('utf-8', 'ignore')
    return msg.get_payload(decode=True).decode('utf-8', 'ignore')


async def send_reply(sender_email, subject, body):
    """Envía email respuesta asíncrona."""
    try:
        msg = email.message.Message()
        msg['From'] = EMAIL_ACCOUNT
        msg['To'] = sender_email
        msg['Subject'] = f"Re: {subject}"
        msg.add_header('Content-Type', 'text/plain; charset=UTF-8')
        msg.set_payload(body.encode('utf-8'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info(f"Respuesta enviada a {sender_email}")
    except Exception as e:
        logger.error(f"Error al enviar email de respuesta: {e}")


async def process_emails():
    """Procesa emails no leídos, obtiene respuesta IA y contesta."""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        mail.select("inbox")
        _, data = mail.search(None, "UNSEEN")
        mail_ids = data[0].split()

        if not mail_ids:
            logger.info("No hay emails nuevos.")
            mail.logout()
            return

        logger.info(f"Se encontraron {len(mail_ids)} emails nuevos.")

        async with AsyncSessionLocal() as db_session:
            for mail_id in mail_ids:
                try:
                    _, data = mail.fetch(mail_id, "(RFC822)")
                    msg = email.message_from_bytes(data[0][1])

                    body = get_email_body(msg)
                    sender_email = parseaddr(msg["from"])[1]
                    subject = msg["subject"]

                    logger.info(f"Procesando email de: {sender_email}")

                    # Obtener catálogo y prompt sistema
                    catalog = await ia_services.get_catalog_from_db(db_session)
                    system_prompt = ia_services.get_chatbot_system_prompt()
                    full_system_prompt = f"{system_prompt}\n\n{catalog}"

                    # Construir historial para Gemini: empty porque email
                    gemini_history = []

                    # Usar get_gemini_response adecuadamente: (system_prompt, history, pregunta)
                    ai_response = ia_services.get_gemini_response(full_system_prompt, gemini_history, body)

                    # Enviar respuesta
                    await send_reply(sender_email, subject, ai_response)

                    # Marcar como leído
                    mail.store(mail_id, '+FLAGS', '\\Seen')

                except Exception as e:
                    logger.error(f"Error al procesar email ID {mail_id}: {e}")

        mail.logout()

    except Exception as e:
        logger.error(f"Error en el ciclo principal del worker: {e}")


async def main():
    logger.info("Iniciando worker de emails... Presiona CTRL+C para detener.")
    while True:
        try:
            await process_emails()
            logger.info("Esperando 2 minutos para el próximo chequeo...")
            await asyncio.sleep(120)
        except KeyboardInterrupt:
            logger.info("Deteniendo el worker de emails.")
            break


if __name__ == "__main__":
    asyncio.run(main())
