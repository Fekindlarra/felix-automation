#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Brevo Email Service
Envía PDFs de auditorías automáticamente por email
"""

import os
import httpx
import base64
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr
from datetime import datetime
import logging

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════

BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
BREVO_API_URL = "https://api.brevo.com/v3"
FROM_EMAIL = "auditorias@enbuenamesa.com"
FROM_NAME = "Felix - Auditorías Automáticas"

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# MODELOS PYDANTIC
# ═══════════════════════════════════════════════════════════════════════════

class Recipient(BaseModel):
    """Destinatario del email"""
    email: EmailStr
    name: Optional[str] = None

class EmailAttachment(BaseModel):
    """Attachment de email"""
    name: str  # Nombre del archivo
    content: str  # Base64 encoded
    content_type: str = "application/pdf"

class BrevoEmail(BaseModel):
    """Email a enviar por Brevo"""
    to: List[Recipient]
    subject: str
    html_content: str
    text_content: Optional[str] = None
    attachment: Optional[EmailAttachment] = None
    reply_to: Optional[Recipient] = None

# ═══════════════════════════════════════════════════════════════════════════
# CLIENTE DE BREVO
# ═══════════════════════════════════════════════════════════════════════════

class BrevoClient:
    """Cliente para enviar emails por Brevo"""

    def __init__(self, api_key: str = BREVO_API_KEY):
        self.api_key = api_key
        self.base_url = BREVO_API_URL
        self.client = httpx.AsyncClient(timeout=30.0)

    async def send_email(self, email: BrevoEmail) -> Dict[str, Any]:
        """
        Envía un email por Brevo

        Args:
            email: Email a enviar

        Returns:
            Respuesta de Brevo con message_id
        """

        try:
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "api-key": self.api_key
            }

            # Construir payload
            payload = {
                "to": [
                    {
                        "email": recipient.email,
                        "name": recipient.name or recipient.email.split("@")[0]
                    }
                    for recipient in email.to
                ],
                "sender": {
                    "email": FROM_EMAIL,
                    "name": FROM_NAME
                },
                "subject": email.subject,
                "htmlContent": email.html_content,
                "textContent": email.text_content or email.subject
            }

            # Agregar attachment si existe
            if email.attachment:
                payload["attachment"] = [
                    {
                        "name": email.attachment.name,
                        "content": email.attachment.content,
                        "contentType": email.attachment.content_type
                    }
                ]

            # Agregar reply_to si existe
            if email.reply_to:
                payload["replyTo"] = {
                    "email": email.reply_to.email,
                    "name": email.reply_to.name or email.reply_to.email
                }

            # Enviar
            response = await self.client.post(
                f"{self.base_url}/smtp/email",
                json=payload,
                headers=headers
            )

            if response.status_code != 201:
                raise Exception(
                    f"Brevo error: {response.status_code} - {response.text}"
                )

            result = response.json()
            return {
                "status": "sent",
                "message_id": result.get("messageId"),
                "timestamp": datetime.utcnow().isoformat()
            }

        except httpx.RequestError as e:
            raise Exception(f"Brevo connection error: {str(e)}")
        except Exception as e:
            raise Exception(f"Brevo send error: {str(e)}")

    async def close(self):
        """Cierra la conexión"""
        await self.client.aclose()

# ═══════════════════════════════════════════════════════════════════════════
# GENERADOR DE EMAILS
# ═══════════════════════════════════════════════════════════════════════════

class AuditEmailGenerator:
    """Genera emails con auditorías adjuntas"""

    @staticmethod
    def build_audit_email(
        cliente_email: str,
        cliente_nombre: str,
        auditoria_nombre: str,
        pdf_bytes: bytes,
        score: float
    ) -> BrevoEmail:
        """
        Construye un email con el PDF de auditoría

        Args:
            cliente_email: Email del cliente
            cliente_nombre: Nombre del cliente
            auditoria_nombre: Nombre de la auditoría
            pdf_bytes: Bytes del PDF
            score: Score general (0-100)

        Returns:
            BrevoEmail listo para enviar
        """

        # Encodear PDF a base64
        pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')

        # Determinar tono basado en score
        if score >= 75:
            emoji = "✅"
            tono = "excelente"
        elif score >= 50:
            emoji = "⚠️"
            tono = "regular"
        else:
            emoji = "❌"
            tono = "necesita mejoras"

        # HTML del email
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background: #f9fafb;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    padding: 40px;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    border-bottom: 2px solid #3b82f6;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    color: #3b82f6;
                    margin: 0 0 10px 0;
                    font-size: 28px;
                }}
                .header p {{
                    color: #666;
                    margin: 0;
                    font-size: 14px;
                }}
                .score-box {{
                    background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 8px;
                    text-align: center;
                    margin: 30px 0;
                }}
                .score-box .emoji {{
                    font-size: 48px;
                    margin-bottom: 10px;
                }}
                .score-box .number {{
                    font-size: 56px;
                    font-weight: bold;
                    margin: 10px 0;
                }}
                .score-box .text {{
                    font-size: 16px;
                    opacity: 0.9;
                }}
                .content {{
                    margin: 30px 0;
                }}
                .content p {{
                    margin: 15px 0;
                    color: #555;
                    text-align: justify;
                }}
                .button {{
                    display: inline-block;
                    background: #f59e0b;
                    color: white;
                    padding: 12px 30px;
                    border-radius: 6px;
                    text-decoration: none;
                    margin: 20px 0;
                    font-weight: bold;
                }}
                .footer {{
                    border-top: 1px solid #e5e7eb;
                    padding-top: 20px;
                    margin-top: 30px;
                    text-align: center;
                    color: #999;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Felix Auditorías</h1>
                    <p>Tu auditoría está lista</p>
                </div>

                <div class="score-box">
                    <div class="emoji">{emoji}</div>
                    <div class="number">{score:.1f}</div>
                    <div class="text">SCORE GENERAL - Resultado {tono}</div>
                </div>

                <div class="content">
                    <p>¡Hola <strong>{cliente_nombre}</strong>!</p>

                    <p>Tu auditoría de <strong>{auditoria_nombre}</strong> ha sido completada exitosamente.</p>

                    <p><strong>✓ Score General: {score:.1f}/100</strong></p>

                    <p>El reporte incluye:</p>
                    <ul>
                        <li>Resumen ejecutivo</li>
                        <li>Hallazgos principales</li>
                        <li>Recomendaciones accionables</li>
                        <li>Detalles técnicos</li>
                        <li>Próximos pasos sugeridos</li>
                    </ul>

                    <p>Adjunto encontrarás el PDF completo con todos los detalles.</p>

                    <p><strong>Próximas auditorías:</strong> La próxima auditoría está programada para la próxima semana. Recibirás un nuevo reporte automáticamente.</p>
                </div>

                <div class="footer">
                    <p>Felix - Auditorías Automáticas</p>
                    <p>Sistema automático de análisis y reportería</p>
                    <p>© 2026 En Buena Mesa. Todos los derechos reservados.</p>
                    <p><a href="https://enbuenamesa.com" style="color: #3b82f6; text-decoration: none;">www.enbuenamesa.com</a></p>
                </div>
            </div>
        </body>
        </html>
        """

        # Crear attachment
        attachment = EmailAttachment(
            name=f"{auditoria_nombre.replace(' ', '_')}.pdf",
            content=pdf_b64,
            content_type="application/pdf"
        )

        # Crear email
        return BrevoEmail(
            to=[Recipient(email=cliente_email, name=cliente_nombre)],
            subject=f"{emoji} Tu auditoría está lista: {auditoria_nombre}",
            html_content=html_content,
            attachment=attachment,
            reply_to=Recipient(
                email=FROM_EMAIL,
                name=FROM_NAME
            )
        )

# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES DE PRUEBA
# ═══════════════════════════════════════════════════════════════════════════

async def test_email_sending():
    """Test del envío de emails"""

    client = BrevoClient()

    # Crear email de prueba
    email = AuditEmailGenerator.build_audit_email(
        cliente_email="felipe@enbuenamesa.com",
        cliente_nombre="Felipe Kind",
        auditoria_nombre="Luz Agencia Instagram Audit",
        pdf_bytes=b"PDF mock content",  # En producción sería el PDF real
        score=75.5
    )

    try:
        print("📧 Enviando email de prueba...")
        result = await client.send_email(email)
        print(f"✅ Email enviado: {result}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        await client.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_email_sending())
