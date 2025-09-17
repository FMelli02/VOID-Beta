import pytest
from unittest.mock import patch, AsyncMock
from email.mime.text import MIMEText

from BACKEND.services.email_service import send_order_confirmation_email

@pytest.mark.asyncio
async def test_send_order_confirmation_email():
    """
    Prueba que la función de email de confirmación de orden llama al
    método de envío de aiosmtplib con los parámetros correctos, sin
    enviar un email real.
    """
    # Información de pago simulada
    mock_payment_info = {
        "payer": {"email": "comprador@test.com"},
        "transaction_amount": 123.45,
    }

    # Simula (mock) la función aiosmtplib.send en el módulo donde se usa
    with patch('BACKEND.services.email_service.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
        await send_order_confirmation_email(mock_payment_info)

        # Verifica que fue aguardado una vez
        mock_send.assert_awaited_once()

        # Usa la API de mock para obtener args/kwargs correctamente
        call = mock_send.call_args
        
        # --- ACÁ ESTÁ LA CORRECCIÓN ---
        # El objeto del mensaje es el primer argumento posicional (índice 0).
        sent_message = call.args[0] 
        # No necesitás el segundo [0]

        # Cabeceras básicas
        assert sent_message["To"] == "comprador@test.com"
        assert sent_message["Subject"] == "¡Gracias por tu compra en VOID!"

        # Extrae la parte HTML de forma robusta
        html_content = None
        payload = sent_message.get_payload()

        if isinstance(payload, list):
            for part in payload:
                if isinstance(part, MIMEText) and part.get_content_subtype() == "html":
                    html_content = part.get_payload(decode=True).decode("utf-8")
                    break
        else:
            if sent_message.get_content_subtype() == "html":
                html_content = sent_message.get_payload(decode=True).decode("utf-8")

        assert html_content is not None
        assert "Total: $123.45" in html_content