"""
Envío de correos transaccionales (bienvenida, etc.).

Usa SMTP estándar (smtplib). Si SMTP no está configurado en el entorno, el
envío se omite de forma segura — nunca debe romper el flujo de registro.
"""
import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional

from app.core.config import settings


def _smtp_configured() -> bool:
    return bool(settings.smtp_host and settings.smtp_user and settings.smtp_password)


def send_email(
    to: str,
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
) -> bool:
    """
    Envía un correo. Devuelve True si se envió, False si se omitió o falló.
    Nunca lanza excepción: el envío de correo es best-effort.
    """
    if not _smtp_configured():
        print(f"[email] SMTP no configurado; correo a {to} omitido ({subject!r})")
        return False

    msg = EmailMessage()
    msg["From"] = settings.smtp_from or settings.smtp_user
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body_text)
    if body_html:
        msg.add_alternative(body_html, subtype="html")

    try:
        if settings.smtp_use_tls:
            # STARTTLS (típico en el puerto 587)
            context = ssl.create_default_context()
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
                server.starttls(context=context)
                server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)
        else:
            # SSL directo (típico en el puerto 465)
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(
                settings.smtp_host, settings.smtp_port, timeout=15, context=context
            ) as server:
                server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)
        return True
    except Exception as e:
        print(f"[email] Error enviando correo a {to}: {type(e).__name__}: {e}")
        return False


def send_welcome_email(to: str, name: str) -> bool:
    """Correo de bienvenida que se envía cuando un usuario se registra."""
    subject = "¡Bienvenido a Combat Analyzer Pro! ⚔️"
    safe_name = name or "entrenador"

    body_text = (
        f"Hola {safe_name},\n\n"
        "¡Tu cuenta en Combat Analyzer Pro ya está lista!\n\n"
        "Desde ahora puedes registrar peleadores, analizar videos de combate y "
        "generar planes estratégicos para tus próximas peleas.\n\n"
        "Empieza creando tu primer peleador y subiendo un video o enlace de YouTube "
        "para obtener un scouting táctico completo.\n\n"
        "¡A ganar!\n"
        "El equipo de Combat Analyzer Pro"
    )

    body_html = f"""\
<div style="font-family:Arial,Helvetica,sans-serif;max-width:520px;margin:0 auto;color:#1f2937">
  <h1 style="color:#0f172a">⚔️ Combat Analyzer Pro</h1>
  <p>Hola <strong>{safe_name}</strong>,</p>
  <p>¡Tu cuenta ya está lista! Desde ahora puedes:</p>
  <ul>
    <li>Registrar peleadores (nuestros y oponentes)</li>
    <li>Analizar videos de combate o enlaces de YouTube</li>
    <li>Generar planes estratégicos para tus próximas peleas</li>
  </ul>
  <p>Empieza creando tu primer peleador y subiendo un video para obtener un
     scouting táctico completo.</p>
  <p style="margin-top:24px">¡A ganar!<br>
     <span style="color:#6b7280">El equipo de Combat Analyzer Pro</span></p>
</div>"""

    return send_email(to, subject, body_text, body_html)
