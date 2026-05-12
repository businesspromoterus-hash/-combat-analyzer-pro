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

    # AI Engines
    gemini_api_key: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    default_video_engine: str = "gemini"
    default_strategy_engine: str = "claude"

    # Database
    database_url: str = "sqlite:///./combat.db"

    # Files
    upload_dir: str = "./uploads"
    reports_dir: str = "./reports"
    max_video_size_mb: int = 500

    # Limits
    max_fights_per_fighter: int = 10
    analysis_timeout_seconds: int = 600

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
