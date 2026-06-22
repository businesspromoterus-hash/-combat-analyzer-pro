"""
Motor Gemini OPTIMIZADO para velocidad máxima.
Usa google-generativeai async nativo para evitar timeouts de Railway.
Modelo: gemini-2.0-flash
"""
import os
import json
import re
import asyncio
from typing import Optional

import google.generativeai as genai
from google.generativeai import GenerativeModel

from app.core.config import settings
from app.engines.base import (
    BaseVideoEngine,
    FightAnalysisResult,
    FighterStyleProfile,
)

FIGHT_ANALYSIS_PROMPT = """
Eres un analista de deportes de combate de élite con acceso al video completo.

PELEADOR A ANALIZAR: {fighter_name}
DEPORTE: {sport}
{coach_notes_block}

INSTRUCCIÓN CRÍTICA — TIMESTAMPS:
Para CADA observación táctica positiva o negativa DEBES indicar:
- En qué ROUND ocurre
- En qué MINUTO aproximado (ej: "Round 3, min 1:20")
- Si es patrón repetido, menciona TODOS los momentos

INSTRUCCIÓN DE ENRIQUECIMIENTO:
Indica si cada observación:
- CONFIRMA lo conocido públicamente
- CONTRADICE lo conocido
- ES NUEVO — no reportado públicamente

Genera el análisis completo en JSON:

{{
  "fighter_name": "{fighter_name}",
  "fight_summary": "resumen de la pelea y resultado",

  "context_validation": {{
    "confirms_public_knowledge": ["observación con timestamp"],
    "contradicts_public_knowledge": ["observación con timestamp"],
    "new_discoveries": ["patrón nuevo con timestamp"]
  }},

  "offensive_patterns": {{
    "favorite_strikes": ["técnica — Round X min Y:ZZ"],
    "entry_patterns": ["patrón con timestamp"],
    "combination_sequences": ["combinación con timestamp"],
    "clinch_offense": "descripción con timestamps",
    "takedown_offense": "descripción con timestamps si aplica",
    "ground_offense": "descripción con timestamps si aplica"
  }},

  "defensive_patterns": {{
    "primary_defense": "sistema defensivo principal",
    "head_movement": "descripción con timestamps",
    "footwork_defense": "descripción con timestamps",
    "frequent_defensive_errors": [
      "Error — Round X min Y:ZZ, Round A min B:CC"
    ],
    "vulnerable_angles": ["ángulo con timestamp"],
    "clinch_defense": "descripción con timestamps",
    "takedown_defense": "descripción con timestamps si aplica"
  }},

  "physical_attributes": {{
    "cardio_assessment": "evaluación con timestamps",
    "power_level": "con timestamps de momentos de poder",
    "chin_durability": "con timestamps de impactos recibidos",
    "speed_assessment": "con timestamps",
    "strength_in_clinch": "con timestamps"
  }},

  "mental_game": {{
    "pressure_response": "con timestamps",
    "dominant_response": "con timestamps",
    "adversity_handling": "con timestamps",
    "corner_instruction_response": "con timestamps de ajustes visibles",
    "risk_taking": "con timestamps"
  }},

  "round_by_round_notes": {{
    "round_1": "análisis con momentos clave",
    "round_2": "análisis",
    "round_3": "análisis",
    "round_4_plus": "rounds intermedios con timestamps",
    "late_rounds": "rounds finales con timestamps",
    "rhythm_drops": ["bajón con timestamp y contexto"]
  }},

  "key_moments": [
    {{
      "round": 3,
      "timestamp": "1:45",
      "type": "weakness",
      "description": "descripción del momento",
      "public_context": "conocido/nuevo descubrimiento",
      "importance": "alta/media/baja"
    }}
  ],

  "fight_result_analysis": {{
    "result": "ganó/perdió/empate",
    "why_won_or_lost": "análisis con timestamps",
    "turning_point": "Round X min Y:ZZ",
    "adjustments_made": "con timestamps"
  }},

  "strengths": [
    "Fortaleza — Round X min Y — confirma/nuevo"
  ],

  "weaknesses": [
    "Debilidad — Round X min Y — conocida/nueva"
  ],

  "intelligence_summary": "resumen combinando video + contexto público"
}}

Responde SOLO con el JSON. Sin markdown.
""".strip()

SCOUTING_SYNTHESIS_PROMPT = """
Eres el jefe de scouting de un equipo de combate de élite.

Recibes {num_fights} análisis de peleas de {fighter_name} ({sport}).
Cada análisis incluye timestamps y contexto de internet.

DATOS BIO: {bio_data}

ANÁLISIS:
{analyses_text}

Genera el reporte completo en JSON:

{{
  "fighter_name": "{fighter_name}",
  "sport": "{sport}",
  "fights_reviewed": {num_fights},
  "intelligence_confidence": "alta/media/baja",
  "overall_style": "descripción completa",
  "consistent_strengths": ["fortaleza con timestamps de múltiples peleas", "mínimo 6"],
  "consistent_weaknesses": ["debilidad con timestamps múltiples", "mínimo 6"],
  "signature_techniques": ["técnica con timestamps", "mínimo 5"],
  "recurring_defensive_errors": ["error con timestamps múltiples", "mínimo 4"],
  "key_moments_across_fights": [
    {{
      "fight": "vs Rival",
      "round": 3,
      "timestamp": "1:45",
      "type": "weakness",
      "description": "descripción",
      "source": "video/video+internet/internet"
    }}
  ],
  "confirmed_by_multiple_sources": ["patrón confirmado en video e internet"],
  "new_discoveries_video_only": ["patrón nuevo solo en video"],
  "contradictions_found": ["contradice reputación pública"],
  "cardio_profile": "evaluación con timestamps",
  "late_round_behavior": "con timestamps",
  "rhythm_drop_patterns": ["patrón con timestamps múltiples peleas"],
  "mental_profile": "con timestamps",
  "corner_adaptability": "con evidencia de video",
  "strategy_evolution": "con evidencia",
  "historical_losses_pattern": "con referencias",
  "historical_wins_pattern": "con referencias",
  "matchup_history_vs_similar": "con timestamps",
  "orthodox_vs_southpaw": "con timestamps",
  "summary": "resumen ejecutivo 5-6 oraciones"
}}

Responde SOLO con el JSON. Sin markdown.
""".strip()


def get_best_gemini_model() -> str:
    configured = os.getenv("GEMINI_MODEL", "")
    if configured:
        return configured
    return "gemini-2.5-flash"


class GeminiEngine(BaseVideoEngine):
    """
    Motor Gemini OPTIMIZADO.
    Usa generate_content_async nativo para máxima velocidad.
    No usa asyncio.to_thread — llamada directamente asíncrona.
    """

    name = "gemini"
    MODEL = get_best_gemini_model()

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY no configurada")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._model = GenerativeModel(self.MODEL)

    async def analyze_fight_video(
        self,
        video_source: str,
        fighter_name: str,
        sport: str,
        coach_notes: Optional[str] = None,
    ) -> FightAnalysisResult:

        coach_block = f"\nNOTAS DEL ENTRENADOR: {coach_notes}" if coach_notes else ""

        prompt = FIGHT_ANALYSIS_PROMPT.format(
            fighter_name=fighter_name,
            sport=sport,
            coach_notes_block=coach_block,
        )

        if video_source.startswith("http"):
            contents = [prompt, {"file_data": {"mime_type": "video/*", "file_uri": video_source}}]
        else:
            # Video local — subir con File API
            video_file = await asyncio.to_thread(
                genai.upload_file, video_source
            )
            contents = [prompt, video_file]

        # ← CLAVE: generate_content_async en lugar de asyncio.to_thread
        response = await self._model.generate_content_async(
            contents,
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 8192,
            }
        )

        raw = response.text.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        data = json.loads(raw)
        return FightAnalysisResult(**data)

    async def synthesize_fighter_profile(
        self,
        fighter_name: str,
        sport: str,
        individual_analyses: list[FightAnalysisResult],
        bio_data: Optional[dict] = None,
    ) -> FighterStyleProfile:

        analyses_text = "\n\n".join(
            f"=== PELEA {i+1} ===\n{json.dumps(a.model_dump(), ensure_ascii=False, indent=2)}"
            for i, a in enumerate(individual_analyses)
        )

        prompt = SCOUTING_SYNTHESIS_PROMPT.format(
            fighter_name=fighter_name,
            sport=sport,
            num_fights=len(individual_analyses),
            bio_data=json.dumps(bio_data or {}, ensure_ascii=False),
            analyses_text=analyses_text,
        )

        # ← CLAVE: generate_content_async
        response = await self._model.generate_content_async(
            prompt,
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 8192,
            }
        )

        raw = response.text.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        data = json.loads(raw)
        return FighterStyleProfile(**data)
