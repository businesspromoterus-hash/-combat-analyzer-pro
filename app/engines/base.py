"""
Interfaz abstracta para motores de IA.

Cualquier motor (Gemini, Claude, OpenAI, futuros) debe implementar esta interfaz.
Esto permite intercambiar motores sin cambiar el resto del código.
"""
from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel


# ========== ESQUEMAS DE SALIDA ESTANDARIZADOS ==========

class FightAnalysisResult(BaseModel):
    """Resultado estructurado del análisis de UNA pelea (generado por Gemini)."""
    # Identidad
    fighter_name: str
    sport: str

    # Estilo general
    fighting_style: str
    primary_stance_behavior: str

    # Fortalezas y debilidades
    strengths: list[str]
    weaknesses: list[str]

    # Patrones técnicos
    repeated_patterns: list[str]
    favorite_techniques: list[str]
    defensive_errors: list[str]
    when_hand_drops: Optional[str] = None         # ¿cuándo baja la mano específicamente?

    # Estado físico y mental
    cardio_assessment: str
    pressure_response: str
    late_rounds_behavior: str
    fatigue_signs: Optional[str] = None           # señales visibles de cansancio
    mental_state: Optional[str] = None            # estado mental durante la pelea

    # Comportamiento según guardia del rival
    vs_orthodox: Optional[str] = None             # vs derechos
    vs_southpaw: Optional[str] = None             # vs zurdos

    # Golpes/técnicas recibidos
    shots_received_most: list[str] = []           # qué le pegan más

    # Movimiento y defensa
    movement_pattern: Optional[str] = None        # cómo se mueve
    defense_style: Optional[str] = None           # cómo defiende

    # Análisis de esquina y ajustes
    corner_instructions: Optional[str] = None     # instrucciones de la esquina
    between_rounds_adjustments: Optional[str] = None  # qué ajusta o no entre rounds

    # Resultado causal
    win_loss_cause: Optional[str] = None          # por qué ganó o perdió esta pelea

    # Momentos clave
    key_moments: list[dict] = []                  # [{timestamp, description, importance}]

    # Riesgos
    danger_signs: list[str] = []

    # Meta
    confidence: float = 0.7
    notes: Optional[str] = None


class FighterStyleProfile(BaseModel):
    """Síntesis táctica de un peleador (agregada de múltiples peleas)."""
    fighter_name: str
    overall_style: str
    consistent_strengths: list[str]
    consistent_weaknesses: list[str]
    signature_techniques: list[str]
    recurring_defensive_holes: list[str]
    cardio_profile: str
    mental_profile: str                    # cómo responde a presión, adversidad
    historical_losses_pattern: str         # cómo ha perdido históricamente
    matchup_history_vs_similar: str        # vs peleadores con perfil similar al nuestro
    summary: str


class CompleteFightPlan(BaseModel):
    """Plan estratégico completo para una pelea."""
    # Comparación estilos
    style_matchup: dict                    # nuestro estilo vs su estilo
    physical_matchup: dict                 # altura, alcance, edad, etc.
    tactical_advantages: list[str]
    tactical_risks: list[str]

    # Planes
    plan_a: dict                           # plan principal
    plan_b: dict                           # plan alternativo
    plan_c: dict                           # plan de emergencia

    # Estrategia por rounds
    rounds_strategy: list[dict]            # [{round, focus, do, avoid}]

    # Tácticas específicas
    recommended_techniques: list[str]
    techniques_to_avoid: list[str]
    when_to_press: str
    when_to_exit: str
    when_to_clinch: str
    attack_approach: str
    defense_approach: str

    # Plan del rival (lo que el oponente probablemente intentará)
    opponent_likely_plan: dict

    # Contramedidas
    countermeasures: list[dict]            # [{if_opponent_does, our_response}]

    # Sparrings recomendados
    sparring_profiles: list[dict]          # [{type, why, priority}]

    # Plan de campamento
    camp_plan: dict                        # {physical, technical, tactical, focus}

    # Resumen ejecutivo
    executive_summary: str


# ========== INTERFAZ DEL MOTOR ==========

class AIEngine(ABC):
    """Interfaz que todos los motores deben implementar."""

    name: str = "base"
    supports_video: bool = False
    supports_strategy: bool = False
    supports_vision: bool = False

    @abstractmethod
    async def analyze_fight_video(
        self,
        video_source: str,        # path local o URL
        fighter_name: str,
        sport: str,
        coach_notes: Optional[str] = None,
    ) -> FightAnalysisResult:
        """Analiza una pelea (video o link) y devuelve análisis estructurado."""
        raise NotImplementedError

    @abstractmethod
    async def synthesize_fighter_profile(
        self,
        fighter_name: str,
        sport: str,
        individual_analyses: list[FightAnalysisResult],
        bio_data: dict,
    ) -> FighterStyleProfile:
        """Toma múltiples análisis individuales y los sintetiza en perfil consolidado."""
        raise NotImplementedError

    @abstractmethod
    async def generate_fight_plan(
        self,
        our_profile: FighterStyleProfile,
        our_bio: dict,
        opponent_profile: FighterStyleProfile,
        opponent_bio: dict,
        sport: str,
        additional_context: Optional[str] = None,
    ) -> CompleteFightPlan:
        """Genera plan estratégico completo cruzando ambos perfiles."""
        raise NotImplementedError

    # Predicción de pelea. No es abstracto para no obligar a todos los motores;
    # los motores de estrategia (Claude) lo sobreescriben.
    async def predict_fight(
        self,
        our_bio: dict,
        opponent_bio: dict,
        sport: str,
        our_context: Optional[dict] = None,
        opponent_context: Optional[dict] = None,
    ) -> dict:
        """Predice ganador probable, método y ronda estimada."""
        raise NotImplementedError(
            f"{self.name} no soporta predicción de pelea; usa Claude."
        )


# ========== BASES ESPECIALIZADAS ==========
# Los motores concretos heredan de estas bases según su especialidad:
#   GeminiEngine -> BaseVideoEngine ; ClaudeEngine -> BaseStrategyEngine.
# Antes no existían y provocaban al importar los motores:
#   ImportError: cannot import name 'BaseVideoEngine' from 'app.engines.base'

class BaseVideoEngine(AIEngine):
    """
    Base para motores con análisis de video nativo (p. ej. Gemini).

    Implementa por defecto generate_fight_plan (que estos motores no usan)
    para que la subclase deje de ser abstracta y pueda instanciarse.
    """
    supports_video = True
    supports_strategy = True

    async def generate_fight_plan(
        self,
        our_profile: FighterStyleProfile,
        our_bio: dict,
        opponent_profile: FighterStyleProfile,
        opponent_bio: dict,
        sport: str,
        additional_context: Optional[str] = None,
    ) -> CompleteFightPlan:
        raise NotImplementedError(
            f"{self.name} es un motor de video; usa un motor de estrategia "
            "(p. ej. Claude) para generar planes."
        )


class BaseStrategyEngine(AIEngine):
    """
    Base para motores centrados en razonamiento estratégico (p. ej. Claude).

    Implementa por defecto analyze_fight_video (que estos motores no usan)
    para que la subclase deje de ser abstracta y pueda instanciarse.
    """
    supports_video = False
    supports_strategy = True

    async def analyze_fight_video(
        self,
        video_source: str,
        fighter_name: str,
        sport: str,
        coach_notes: Optional[str] = None,
    ) -> FightAnalysisResult:
        raise NotImplementedError(
            f"{self.name} no procesa video; usa un motor de video "
            "(p. ej. Gemini) para analizar peleas."
        )
