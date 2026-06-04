"""
Configuración global de la aplicación.
Carga variables de entorno desde .env
"""
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "Combat Analyzer Pro"
    app_version: str = "0.1.0"
    environment: str = "development"
    secret_key: str = "change-me"
    # Secreto de sesión (variable de entorno SESSION_SECRET en Railway).
    # Usado como secreto canónico para la firma/seguridad de sesiones.
    session_secret: str = ""

    # AI Engines
    gemini_api_key: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    default_video_engine: str = "gemini"
    default_strategy_engine: str = "claude"

    # Database
    database_url: str = "sqlite:///./combat.db"

    # Email (correo de bienvenida y transaccionales).
    # Si no se configura SMTP, el envío se omite silenciosamente (no es fatal).
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""          # remitente; por defecto usa smtp_user
    smtp_use_tls: bool = True    # True: STARTTLS (587); False: SSL directo (465)

    # Files
    upload_dir: str = "./uploads"
    reports_dir: str = "./reports"
    max_video_size_mb: int = 500

    # Limits
    max_fights_per_fighter: int = 10
    analysis_timeout_seconds: int = 600

    # ── Aliases en MAYÚSCULAS ─────────────────────────────────────────────
    # Gran parte del código (engines, chat, fighter_search) accede a las
    # claves como settings.ANTHROPIC_API_KEY / GEMINI_API_KEY / OPENAI_API_KEY.
    # Los campos de pydantic-settings son en minúscula, por lo que ese acceso
    # lanzaba AttributeError y rompía autofill, análisis y chat. Exponemos
    # alias en mayúsculas que devuelven el mismo valor.
    @property
    def ANTHROPIC_API_KEY(self) -> str:
        return self.anthropic_api_key

    @property
    def GEMINI_API_KEY(self) -> str:
        return self.gemini_api_key

    @property
    def OPENAI_API_KEY(self) -> str:
        return self.openai_api_key

    @property
    def SESSION_SECRET(self) -> str:
        """Secreto de sesión efectivo (SESSION_SECRET, o secret_key como respaldo)."""
        return self.session_secret or self.secret_key

    @property
    def upload_path(self) -> Path:
        p = Path(self.upload_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def reports_path(self) -> Path:
        p = Path(self.reports_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
