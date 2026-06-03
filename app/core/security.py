"""
Seguridad: hash de contraseñas y manejo de sesiones.
"""
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from app.core.config import settings


def hash_password(password: str) -> str:
    """Hash seguro de contraseña con salt."""
    salt = secrets.token_hex(32)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=260000,
    )
    return f"{salt}:{key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica contraseña contra el hash guardado."""
    try:
        salt, key_hex = hashed_password.split(":")
        key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations=260000,
        )
        return hmac.compare_digest(key.hex(), key_hex)
    except Exception:
        return False


def create_session_token() -> str:
    """Genera un token de sesión único y seguro."""
    return secrets.token_urlsafe(64)
