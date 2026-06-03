"""
Motor Claude: genera el plan estratégico de combate completo.
Recibe los reportes de scouting de Gemini y construye la estrategia ganadora.
"""
import json
import re
import asyncio
from typing import Optional

import anthropic

from app.core.config import settings
from app.engines.base import (
    BaseStrategyEngine,
    FighterStyleProfile,
    CompleteFightPlan,
)

FIGHT_PLAN_PROMPT = """
Eres el estratega táctico principal de un equipo de combate de élite.

Recibes los reportes de scouting completos de AMBOS peleadores generados por el analista.
Tu tarea: construir el PLAN ESTRATÉGICO GANADOR más detallado y profesional posible.

DEPORTE: {sport}
{additional_context_block}

════════════════════════════════════════════
NUESTRO PELEADOR — DATOS BIO:
{our_bio}

SCOUTING DE NUESTRO PELEADOR:
{our_profile}
════════════════════════════════════════════

RIVAL — DATOS BIO:
{opp_bio}

SCOUTING DEL RIVAL:
{opp_profile}
════════════════════════════════════════════

PREDICCIÓN DEL COMBATE (basada en el scouting):
Antes de crear el plan, analiza las probabilidades reales del combate.

Genera el plan completo en formato JSON:

{{
  "fight_prediction": {{
    "winner_prediction": "nombre del peleador que probablemente gana",
    "confidence_percentage": 75,
    "method_prediction": "KO/TKO/Decisión/Sumisión/Puntos",
    "reasoning": "análisis detallado de por qué gana ese peleador basado en el scouting",
    "key_factors": ["factor 1 que determinará el resultado", "factor 2", "factor 3"],
    "danger_moments": ["momento peligroso 1 para nuestro peleador", "momento peligroso 2"],
    "opportunity_moments": ["momento de oportunidad 1", "oportunidad 2"]
  }},

  "executive_summary": "resumen ejecutivo del plan — 4-5 oraciones clave",

  "main_strategy": "estrategia principal — descripción detallada del gameplan central",

  "key_advantages_to_exploit": [
    "ventaja táctica 1 — cómo explotarla exactamente",
    "ventaja táctica 2...",
    "mínimo 5 ventajas"
  ],

  "dangers_to_avoid": [
    "peligro 1 — cómo evitarlo",
    "peligro 2...",
    "mínimo 4 peligros"
  ],

  "plan_a": {{
    "name": "nombre del Plan A",
    "description": "descripción detallada",
    "key_tactics": ["táctica 1", "táctica 2", "táctica 3"],
    "target_areas": ["área del cuerpo/técnica a atacar 1", "área 2"],
    "when_to_use": "condiciones para ejecutar este plan"
  }},

  "plan_b": {{
    "name": "nombre del Plan B",
    "description": "descripción — plan alternativo si el A no funciona",
    "key_tactics": ["táctica 1", "táctica 2"],
    "when_to_use": "cuándo cambiar al Plan B"
  }},

  "plan_c": {{
    "name": "nombre del Plan C",
    "description": "plan de emergencia — si estamos en desventaja",
    "key_tactics": ["táctica 1", "táctica 2"],
    "when_to_use": "cuándo cambiar al Plan C"
  }},

  "round_strategy": {{
    "early_rounds": "estrategia detallada para rounds 1-3",
    "mid_rounds": "estrategia para rounds intermedios",
    "late_rounds": "estrategia para rounds finales",
    "championship_rounds": "si aplica — rounds 10-12"
  }},

  "offensive_game_plan": {{
    "primary_attacks": ["ataque principal 1 con setup", "ataque 2..."],
    "combination_sequences": ["combinación 1 a usar", "combinación 2..."],
    "setup_techniques": ["cómo preparar los ataques principales"],
    "clinch_strategy": "estrategia en el clinch",
    "distance_control": "cómo controlar la distancia"
  }},

  "defensive_game_plan": {{
    "primary_defense": "sistema defensivo recomendado",
    "how_to_neutralize_strengths": "cómo neutralizar las fortalezas del rival",
    "exploiting_defensive_errors": ["cómo explotar error defensivo 1 del rival", "error 2..."],
    "counters": ["contraataque 1", "contraataque 2"],
    "angles_to_use": ["ángulo de ataque 1", "ángulo 2"]
  }},

  "conditioning_exploitation": {{
    "cardio_plan": "si el rival tiene problemas de cardio — cómo explotarlo",
    "pace_management": "cómo manejar el ritmo para agotar al rival",
    "pressure_strategy": "cuándo y cómo aplicar presión"
  }},

  "mental_warfare": {{
    "psychological_tactics": ["táctica psicológica 1", "táctica 2"],
    "how_to_frustrate_rival": "cómo frustrar el gameplan del rival",
    "adversity_plan": "plan si estamos en desventaja — cómo recuperar"
  }},

  "opponent_probable_plan": {{
    "expected_strategy": "qué estrategia usará probablemente el rival",
    "expected_attacks": ["ataque esperado 1", "ataque esperado 2"],
    "how_to_counter_their_plan": "cómo neutralizar su gameplan"
  }},

  "corner_instructions": {{
    "between_rounds": "instrucciones tipo para entre rounds",
    "key_adjustments": ["ajuste 1 si X pasa", "ajuste 2 si Y pasa"],
    "when_to_change_plan": "señales para cambiar el plan"
  }},

  "sparring_recommendations": {{
    "sparring_partner_profile": "perfil del sparring ideal para preparar esta pelea",
    "key_situations_to_drill": ["situación 1 a practicar", "situación 2..."],
    "rounds_focus": "en qué tipo de rounds enfocarse"
  }},

  "training_camp_plan": {{
    "physical": "plan físico específico para esta pelea",
    "technical": "trabajo técnico prioritario",
    "tactical": "trabajo táctico-mental",
    "mental": "preparación mental específica"
  }},

  "week_before_fight": "recomendaciones para la semana antes de la pelea",

  "fight_night_checklist": ["punto 1 para la noche de la pelea", "punto 2...", "mínimo 5 puntos"]
}}

Responde SOLO con el JSON. Sin markdown, sin explicaciones.
""".strip()


class ClaudeEngine(BaseStrategyEngine):
    """Motor estratégico usando Claude."""

    name = "claude"
    MODEL = "claude-sonnet-4-20250514"

    def __init__(self):
        if not settings.ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY no configurada")
        self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def synthesize_fighter_profile(
        self,
        fighter_name: str,
        sport: str,
        individual_analyses: list,
        bio_data: Optional[dict] = None,
    ):
        """Claude también puede sintetizar perfiles si se necesita."""
        from app.engines.base import FighterStyleProfile
        analyses_text = "\n\n".join(
            f"=== PELEA {i+1} ===\n{json.dumps(a.model_dump(), ensure_ascii=False, indent=2)}"
            for i, a in enumerate(individual_analyses)
        )

        prompt = f"""
Sintetiza el perfil táctico de {fighter_name} ({sport}) basado en {len(individual_analyses)} peleas analizadas.

ANÁLISIS:
{analyses_text}

Responde en JSON con la estructura de FighterStyleProfile.
Solo JSON, sin markdown.
""".strip()

        response = await asyncio.to_thread(
            self._client.messages.create,
            model=self.MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        data = json.loads(raw)
        return FighterStyleProfile(**data)

    async def generate_fight_plan(
        self,
        our_profile: FighterStyleProfile,
        our_bio: dict,
        opponent_profile: FighterStyleProfile,
        opponent_bio: dict,
        sport: str,
        additional_context: Optional[str] = None,
    ) -> CompleteFightPlan:

        ctx_block = f"\nCONTEXTO ADICIONAL: {additional_context}" if additional_context else ""

        prompt = FIGHT_PLAN_PROMPT.format(
            sport=sport,
            additional_context_block=ctx_block,
            our_bio=json.dumps(our_bio, ensure_ascii=False, indent=2),
            our_profile=json.dumps(our_profile.model_dump(), ensure_ascii=False, indent=2),
            opp_bio=json.dumps(opponent_bio, ensure_ascii=False, indent=2),
            opp_profile=json.dumps(opponent_profile.model_dump(), ensure_ascii=False, indent=2),
        )

        response = await asyncio.to_thread(
            self._client.messages.create,
            model=self.MODEL,
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.content[0].text.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        data = json.loads(raw)
        return CompleteFightPlan(**data)
