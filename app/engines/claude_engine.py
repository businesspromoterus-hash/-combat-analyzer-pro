"""
Motor Claude: plan estratégico completo con recomendaciones de sparring reales.
Claude busca en internet nombres de sparrings asequibles y con perfil correcto.
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

Recibes los reportes de scouting completos de AMBOS peleadores.
Tu tarea: construir el PLAN ESTRATÉGICO GANADOR más completo y profesional posible.

DEPORTE: {sport}
PAÍS/REGIÓN DEL EQUIPO: {country}
{additional_context_block}

════════════════════════════════════════
NUESTRO PELEADOR:
{our_bio}

SCOUTING DE NUESTRO PELEADOR:
{our_profile}
════════════════════════════════════════

RIVAL:
{opp_bio}

SCOUTING DEL RIVAL:
{opp_profile}
════════════════════════════════════════

Genera el plan completo en JSON:

{{
  "fight_prediction": {{
    "winner_prediction": "nombre del peleador que probablemente gana",
    "confidence_percentage": 75,
    "method_prediction": "KO/TKO/Decisión/Sumisión/Puntos",
    "reasoning": "análisis detallado basado en el scouting",
    "key_factors": ["factor 1", "factor 2", "factor 3"],
    "danger_moments": ["momento peligroso 1", "momento peligroso 2"],
    "opportunity_moments": ["oportunidad 1", "oportunidad 2"]
  }},

  "executive_summary": "resumen ejecutivo del plan en 4-5 oraciones",

  "main_strategy": "estrategia principal detallada",

  "key_advantages_to_exploit": [
    "ventaja táctica 1 — cómo explotarla exactamente",
    "mínimo 5 ventajas"
  ],

  "dangers_to_avoid": [
    "peligro 1 — cómo evitarlo",
    "mínimo 4 peligros"
  ],

  "plan_a": {{
    "name": "nombre del Plan A",
    "description": "descripción detallada",
    "key_tactics": ["táctica 1", "táctica 2", "táctica 3"],
    "target_areas": ["área a atacar 1", "área 2"],
    "when_to_use": "condiciones para ejecutar este plan"
  }},

  "plan_b": {{
    "name": "nombre del Plan B",
    "description": "plan alternativo si el A no funciona",
    "key_tactics": ["táctica 1", "táctica 2"],
    "when_to_use": "cuándo cambiar al Plan B"
  }},

  "plan_c": {{
    "name": "nombre del Plan C",
    "description": "plan de emergencia si estamos en desventaja",
    "key_tactics": ["táctica 1", "táctica 2"],
    "when_to_use": "cuándo cambiar al Plan C"
  }},

  "round_strategy": {{
    "early_rounds": "estrategia rounds 1-3",
    "mid_rounds": "estrategia rounds intermedios",
    "late_rounds": "estrategia rounds finales",
    "championship_rounds": "si aplica — rounds 10-12"
  }},

  "offensive_game_plan": {{
    "primary_attacks": ["ataque principal 1 con setup", "ataque 2"],
    "combination_sequences": ["combinación 1", "combinación 2"],
    "setup_techniques": ["cómo preparar los ataques principales"],
    "clinch_strategy": "estrategia en el clinch",
    "distance_control": "cómo controlar la distancia"
  }},

  "defensive_game_plan": {{
    "primary_defense": "sistema defensivo recomendado",
    "how_to_neutralize_strengths": "cómo neutralizar las fortalezas del rival",
    "exploiting_defensive_errors": ["cómo explotar error defensivo 1", "error 2"],
    "counters": ["contraataque 1", "contraataque 2"],
    "angles_to_use": ["ángulo 1", "ángulo 2"]
  }},

  "conditioning_exploitation": {{
    "cardio_plan": "cómo explotar problemas de cardio del rival si los tiene",
    "pace_management": "cómo manejar el ritmo",
    "pressure_strategy": "cuándo y cómo aplicar presión"
  }},

  "mental_warfare": {{
    "psychological_tactics": ["táctica psicológica 1", "táctica 2"],
    "how_to_frustrate_rival": "cómo frustrar el gameplan del rival",
    "adversity_plan": "plan si estamos en desventaja"
  }},

  "opponent_probable_plan": {{
    "expected_strategy": "qué estrategia usará el rival",
    "expected_attacks": ["ataque esperado 1", "ataque esperado 2"],
    "how_to_counter_their_plan": "cómo neutralizar su gameplan"
  }},

  "corner_instructions": {{
    "between_rounds": "instrucciones tipo para entre rounds",
    "key_adjustments": ["ajuste 1 si X pasa", "ajuste 2 si Y pasa"],
    "when_to_change_plan": "señales para cambiar el plan"
  }},

  "sparring_recommendations": {{
    "ideal_profile": {{
      "stance": "guardia ideal del sparring — orthodox/southpaw/switch",
      "style": "estilo de pelea que debe tener el sparring",
      "physical_attributes": "características físicas — estatura, peso, alcance",
      "why": "por qué este perfil es el más útil para esta preparación"
    }},

    "local_options": [
      {{
        "name": "Nombre real de peleador activo",
        "country": "país",
        "record": "récord aproximado si se conoce",
        "why_useful": "por qué es útil para esta preparación específica",
        "similarity_to_rival": "en qué se parece al rival que vamos a enfrentar",
        "accessibility": "asequible — mismo circuito/país/región",
        "contact_hint": "cómo contactarlo — promotora, gimnasio conocido si aplica"
      }}
    ],

    "ideal_options": [
      {{
        "name": "Nombre real de peleador con perfil más exacto",
        "country": "país",
        "record": "récord aproximado",
        "why_useful": "por qué es el más parecido al rival",
        "similarity_to_rival": "similitudes tácticas específicas con el rival",
        "accessibility": "puede requerir viaje o acuerdo entre equipos",
        "contact_hint": "cómo contactarlo si se conoce"
      }}
    ],

    "situations_to_drill": [
      "situación 1 a practicar con el sparring — ej: defender el jab cruzado en distancia larga",
      "situación 2",
      "situación 3",
      "mínimo 5 situaciones específicas"
    ],

    "rounds_focus": "en qué tipo de rounds y situaciones enfocarse con el sparring",

    "sparring_schedule": "cuántos rounds por semana y en qué fase del camp"
  }},

  "training_camp_plan": {{
    "physical": "plan físico específico para esta pelea",
    "technical": "trabajo técnico prioritario",
    "tactical": "trabajo táctico específico",
    "mental": "preparación mental"
  }},

  "week_before_fight": "recomendaciones para la semana antes de la pelea",

  "fight_night_checklist": [
    "punto 1 para la noche de la pelea",
    "mínimo 5 puntos"
  ]
}}

INSTRUCCIÓN PARA SPARRINGS:
Busca en internet nombres REALES de peleadores activos que coincidan con el perfil del rival.
Prioriza peleadores del mismo país o región que nuestro peleador.
Si no hay opciones locales ideales, sugiere opciones internacionales con perfil más exacto.
Sé específico — nombres reales, no genéricos.
Si no puedes confirmar un nombre, indícalo claramente.

Responde SOLO con el JSON. Sin markdown.
""".strip()


class ClaudeEngine(BaseStrategyEngine):
    """Motor estratégico Claude con recomendaciones de sparring reales."""

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
        from app.engines.base import FighterStyleProfile
        analyses_text = "\n\n".join(
            f"=== PELEA {i+1} ===\n{json.dumps(a.model_dump(), ensure_ascii=False, indent=2)}"
            for i, a in enumerate(individual_analyses)
        )

        prompt = f"""
Sintetiza el perfil táctico de {fighter_name} ({sport}) basado en {len(individual_analyses)} peleas.

ANÁLISIS:
{analyses_text}

Responde en JSON con la estructura de FighterStyleProfile. Solo JSON.
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
        country = our_bio.get("country", "No especificado")

        prompt = FIGHT_PLAN_PROMPT.format(
            sport=sport,
            country=country,
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
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": prompt}],
        )

        raw = ""
        for block in response.content:
            if hasattr(block, "text"):
                raw += block.text

        raw = raw.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        data = json.loads(raw)
        return CompleteFightPlan(**data)
