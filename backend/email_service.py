"""
Email Service
Envío de emails para leads, confirmaciones y notificaciones
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os


class EmailService:
    """Servicio de emails basado en SMTP o SendGrid"""

    def __init__(self):
        # Configuración desde variables de entorno
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.sender_email = os.getenv('SENDER_EMAIL', 'tu-email@gmail.com')
        self.sender_password = os.getenv('SENDER_PASSWORD', '')
        self.use_sendgrid = os.getenv('USE_SENDGRID', 'false').lower() == 'true'
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY', '')

        # Intentar importar SendGrid si está disponible
        self.sg = None
        if self.use_sendgrid and self.sendgrid_api_key:
            try:
                from sendgrid import SendGridAPIClient
                self.sg = SendGridAPIClient(self.sendgrid_api_key)
            except ImportError:
                print('SendGrid no instalado. Usando SMTP.')

    def send_email(self, to, subject, body, html=False):
        """
        Enviar email

        Args:
            to: Email destinatario (string o lista)
            subject: Asunto
            body: Cuerpo del mensaje
            html: Si es HTML o texto plano

        Returns:
            bool: True si se envió exitosamente
        """
        try:
            # Si es lista de emails, enviar a cada uno
            if isinstance(to, list):
                for email_addr in to:
                    self.send_email(email_addr, subject, body, html)
                return True

            # Intentar SendGrid primero
            if self.sg:
                return self._send_via_sendgrid(to, subject, body, html)

            # Fallback a SMTP
            return self._send_via_smtp(to, subject, body, html)

        except Exception as e:
            print(f'Error enviando email a {to}: {str(e)}')
            return False

    def _send_via_smtp(self, to, subject, body, html):
        """Enviar vía SMTP (Gmail, etc)"""
        try:
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = to

            # Agregar body
            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))

            # Conectar y enviar
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            print(f'✅ Email enviado a {to}')
            return True

        except Exception as e:
            print(f'❌ Error SMTP: {str(e)}')
            return False

    def _send_via_sendgrid(self, to, subject, body, html):
        """Enviar vía SendGrid API"""
        try:
            from sendgrid.helpers.mail import Mail

            message = Mail(
                from_email=self.sender_email,
                to_emails=to,
                subject=subject,
                plain_text_content=body if not html else None,
                html_content=body if html else None
            )

            response = self.sg.send(message)

            if response.status_code in [200, 201, 202]:
                print(f'✅ Email enviado vía SendGrid a {to}')
                return True
            else:
                print(f'❌ SendGrid error: {response.status_code}')
                return False

        except Exception as e:
            print(f'❌ Error SendGrid: {str(e)}')
            return False

    def send_confirmation_email(self, to, name, company, audit_type):
        """Email de confirmación de lead"""
        subject = '✅ Tu Auditoría Online Está en Proceso'

        body = f"""
<html>
  <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #0F766E;">Hola {name},</h2>

    <p>¡Gracias por solicitar tu auditoría online!</p>

    <div style="background: #F5F5F4; padding: 1.5rem; border-radius: 6px; margin: 1.5rem 0;">
      <h3 style="color: #0F766E; margin-top: 0;">Detalles de tu solicitud:</h3>
      <p><strong>Empresa:</strong> {company}</p>
      <p><strong>Plan:</strong> {audit_type}</p>
      <p><strong>Asunto:</strong> Auditoría Completa de Tu Negocio Online</p>
    </div>

    <h3 style="color: #0F766E;">¿Qué sigue?</h3>
    <ol>
      <li>Nuestro equipo revisará tu solicitud (24 horas)</li>
      <li>Te contactaremos para agendar una llamada breve</li>
      <li>En 48 horas tendrás tu reporte completo en PDF</li>
    </ol>

    <h3 style="color: #0F766E;">Mientras tanto:</h3>
    <ul>
      <li><a href="https://tudominio.com/ejemplos" style="color: #14B8A6;">Ver ejemplos de reportes</a></li>
      <li><a href="https://tudominio.com/casos" style="color: #14B8A6;">Leer casos de éxito</a></li>
      <li><a href="https://tudominio.com/faq" style="color: #14B8A6;">Preguntas frecuentes</a></li>
    </ul>

    <p>Si tienes alguna pregunta urgente, responde este email.</p>

    <p style="color: #14B8A6; font-weight: bold;">¡Vamos a encontrar qué está frenando tus ventas! 🎯</p>

    <hr style="border: none; border-top: 1px solid #E7E5E4; margin: 2rem 0;">

    <p style="font-size: 0.9rem; color: #999;">
      Auditoría Online | En Buena Mesa<br>
      <a href="mailto:felipe@enbuenamesa.com" style="color: #14B8A6;">felipe@enbuenamesa.com</a>
    </p>
  </body>
</html>
        """

        return self.send_email(to, subject, body, html=True)

    def send_alert_email(self, to, title, message):
        """Email de alerta"""
        subject = f'🔔 {title}'

        body = f"""
<html>
  <body style="font-family: Arial, sans-serif;">
    <h2 style="color: #F97316;">{title}</h2>
    <p>{message}</p>
    <p style="font-size: 0.9rem; color: #999;">
      Enviado a las {datetime.now().strftime('%H:%M:%S')} Santiago
    </p>
  </body>
</html>
        """

        return self.send_email(to, subject, body, html=True)


# Instancia global
email_service = EmailService()


def send_email(to, subject, body, html=False):
    """Función helper para enviar emails"""
    return email_service.send_email(to, subject, body, html)
