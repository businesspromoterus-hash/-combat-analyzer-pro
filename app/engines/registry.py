"""
Registro central de motores de IA.

Permite elegir el motor más apropiado para cada tarea y agregar nuevos motores
sin tocar el resto del sistema.

USO RECOMENDADO:
- Análisis de video: Gemini (única con video nativo robusto)
- Síntesis de perfil: Claude (mejor razonamiento sobre múltiples análisis)
- Plan de combate: Claude (mejor razonamiento estratégico multi-paso)
- Backup/comparación: OpenAI

Mario puede sobrescribir desde la API o desde .env.
"""
from typing import Optional
from app.engines.base import AIEngine
from app.core.config import settings


_engines: dict[str, AIEngine] = {}


def get_engine(name: Optional[str] = None) -> AIEngine:
    """
    Obtiene un motor por nombre. Inicialización perezosa.
    Si no se especifica, devuelve el motor por defecto.
    """
    name = (name or settings.default_strategy_engine).lower()

    if name in _engines:
        return _engines[name]

    if name == "gemini":
        from app.engines.gemini_engine import GeminiEngine
        engine = GeminiEngine()
    elif name == "claude":
        from app.engines.claude_engine import ClaudeEngine
        engine = ClaudeEngine()
    elif name == "openai":
        from app.engines.openai_engine import OpenAIEngine
        engine = OpenAIEngine()
    else:
        raise ValueError(f"Motor desconocido: {name}. Opciones: gemini, claude, openai")

    _engines[name] = engine
    return engine


def get_video_engine(name: Optional[str] = None) -> AIEngine:
    """
    Motor recomendado para video: Gemini por defecto.
    Si el motor especificado no soporta video, devuelve igual pero loggea warning.
    """
    engine = get_engine(name or settings.default_video_engine)
    if not engine.supports_video:
        print(f"[WARN] Motor {engine.name} no soporta video nativo, "
              f"análisis será limitado a notas/metadata.")
    return engine


def get_strategy_engine(name: Optional[str] = None) -> AIEngine:
    """Motor recomendado para estrategia/síntesis: Claude por defecto."""
    return get_engine(name or settings.default_strategy_engine)


def list_available_engines() -> list[dict]:
    """Lista todos los motores y sus capacidades."""
    return [
        {"name": "gemini", "video": True, "strategy": True, "vision": True,
         "configured": bool(settings.gemini_api_key)},
        {"name": "claude", "video": False, "strategy": True, "vision": False,
         "configured": bool(settings.anthropic_api_key)},
        {"name": "openai", "video": False, "strategy": True, "vision": True,
         "configured": bool(settings.openai_api_key)},
    ]
