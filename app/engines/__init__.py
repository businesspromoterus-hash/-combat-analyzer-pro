"""Motores de IA intercambiables."""
from app.engines.base import (
    AIEngine, FightAnalysisResult, FighterStyleProfile, CompleteFightPlan
)
from app.engines.registry import (
    get_engine, get_video_engine, get_strategy_engine, list_available_engines
)

__all__ = [
    "AIEngine",
    "FightAnalysisResult",
    "FighterStyleProfile",
    "CompleteFightPlan",
    "get_engine",
    "get_video_engine",
    "get_strategy_engine",
    "list_available_engines",
]
