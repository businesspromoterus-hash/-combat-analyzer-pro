"""
Motor Gemini: análisis de video de peleas.
Modelo: gemini-2.0-flash (estable, soporta video/YouTube)
"""
import json
import re
import asyncio
from typing import Optional

import google.generativeai as genai

from app.core.config import settings
from app.engines.base import (
    BaseVideoEngine,
    FightAnalysisResult,
    FighterStyleProfile,
)

# ── Prompt de análisis de pelea individual ────────────────────────────────────
FIGHT_ANALYSIS_PROMPT = """
Eres un analista de deportes de combate de élite. Observa este video de pelea
con atención al detalle de un scout profesional.

PELEADOR A ANALIZAR: {fighter_name}
DEPORTE: {sport}
{coach_notes_block}

Genera un análisis técnico-táctico COMPLETO y PROFUNDO en formato JSON.
Sé extremadamente específico — menciona momentos concretos del video.

{{
  "fighter_name": "{fighter_name}",
  "fight_summary": "resumen de la pelea y resultado",

  "offensive_patterns": {{
    "favorite_strikes": ["lista detallada de golpes/técnicas favoritas con combinaciones exactas"],
    "entry_patterns": ["cómo entra al ataque — distancia, fintas, paso previo"],
    "combination_sequences": ["secuencias de combinaciones más usadas, ej: jab-cross-gancho-bajo"],
    "clinch_offense": "qué hace en el clinch ofensivamente",
    "takedown_offense": "intentos de derribo — técnica, timing, setup",
    "ground_offense": "trabajo en suelo si aplica"
  }},

  "defensive_patterns": {{
    "primary_defense": "sistema defensivo principal (bloqueo, parry, slip, etc.)",
    "head_movement": "tipo y calidad del movimiento de cabeza",
    "footwork_defense": "cómo usa el movimiento de pies para defenderse",
    "frequent_defensive_errors": ["errores defensivos repetitivos — ej: baja la mano derecha al lanzar jab"],
    "vulnerable_angles": ["ángulos donde queda expuesto"],
    "clinch_defense": "cómo defiende en el clinch",
    "takedown_defense": "calidad y técnica de defensa al derribo"
  }},

  "movement_profile": {{
    "stance": "guardia (orthodox/southpaw/switch)",
    "footwork_style": "descripción del movimiento de pies",
    "ring_generalship": "control del cuadrilátero/área",
    "distance_management": "cómo maneja la distancia",
    "lateral_movement": "movimiento lateral — frecuencia y dirección preferida"
  }},

  "physical_attributes": {{
    "cardio_assessment": "evaluación real del cardio observado en el video",
    "power_level": "nivel de poder — KO power, knockdown, etc.",
    "chin_durability": "resistencia observada a impactos",
    "speed_assessment": "velocidad de manos y pies",
    "strength_in_clinch": "fuerza en cuerpo a cuerpo"
  }},

  "mental_game": {{
    "pressure_response": "cómo reacciona cuando está siendo dominado o lastimado",
    "dominant_response": "cómo reacciona cuando está dominando — ¿presiona o se relaja?",
    "adversity_handling": "respuesta a situaciones difíciles (knockdown, corte, cansancio)",
    "corner_instruction_response": "¿aplica los ajustes de la esquina? ¿en qué round?",
    "risk_taking": "perfil de toma de riesgos"
  }},

  "round_by_round_notes": {{
    "early_rounds": "comportamiento en rounds 1-3",
    "mid_rounds": "comportamiento en rounds intermedios",
    "late_rounds": "comportamiento en rounds finales — ¿sube o baja el nivel?",
    "rhythm_drops": ["momentos específicos donde baja el ritmo"]
  }},

  "fight_result_analysis": {{
    "result": "ganó/perdió/empate",
    "why_won_or_lost": "análisis profundo de por qué ganó o perdió ESTA pelea específica",
    "turning_point": "momento clave que cambió la pelea",
    "adjustments_made": "ajustes que hizo durante la pelea"
  }},

  "strengths": ["lista de 5-8 fortalezas principales observadas"],
  "weaknesses": ["lista de 5-8 debilidades/vulnerabilidades observadas"],

  "key_observations": "observaciones adicionales importantes para el scouting"
}}

Responde SOLO con el JSON. Sin markdown, sin explicaciones.
""".strip()


# ── Prompt de síntesis de scouting (TODAS las peleas) ────────────────────────
SCOUTING_SYNTHESIS_PROMPT = """
Eres el jefe de scouting de un equipo de combate de élite.

Recibes {num_fights} análisis individuales de peleas de {fighter_name} ({sport}).
Tu tarea: sintetizar TODO en un REPORTE DE SCOUTING PROFESIONAL COMPLETO.

No resumas superficialmente. Profundiza. Sé brutalmente honesto.

DATOS BIO: {bio_data}

ANÁLISIS DE PELEAS:
{analyses_text}

Genera el reporte de scouting en formato JSON:

{{
  "fighter_name": "{fighter_name}",
  "sport": "{sport}",
  "fights_reviewed": {num_fights},

  "overall_style": "descripción completa del estilo — en 3-4 oraciones detalladas",

  "consistent_strengths": [
    "fortaleza 1 con explicación detallada y ejemplos de peleas",
    "fortaleza 2...",
    "mínimo 6 fortalezas"
  ],

  "consistent_weaknesses": [
    "debilidad 1 con explicación y cómo explotarla",
    "debilidad 2...",
    "mínimo 6 debilidades"
  ],

  "signature_techniques": [
    "técnica favorita 1 — setup, timing, combinaciones",
    "técnica favorita 2...",
    "mínimo 5 técnicas"
  ],

  "recurring_defensive_errors": [
    "error defensivo 1 — cuándo ocurre, con qué frecuencia",
    "error defensivo 2...",
    "mínimo 4 errores"
  ],

  "strikes_received_most": [
    "golpe que más recibe 1",
    "golpe que más recibe 2"
  ],

  "movement_analysis": "análisis completo del movimiento — footwork, distancia, ring generalship",

  "defense_system": "sistema defensivo completo — qué usa, qué le falta, vulnerabilidades",

  "pressure_response": "cómo responde bajo presión real — análisis honesto",

  "cardio_profile": "evaluación real del cardio basada en peleas — ¿baja en rounds tardíos? ¿cuándo?",

  "late_round_behavior": "comportamiento específico en rounds tardíos — ¿sube, baja, igual?",

  "rhythm_drop_patterns": [
    "patrón de bajón 1 — cuándo y por qué",
    "patrón de bajón 2..."
  ],

  "mental_profile": "perfil mental completo — reacción a adversidad, knockdowns, heridas, cansancio",

  "corner_adaptability": "¿aplica los ajustes de esquina? ¿qué tan bien?",

  "strategy_evolution": "¿cambia la estrategia durante la pelea? ¿cómo?",

  "historical_losses_pattern": "patrón en las derrotas — ¿qué tipo de peleador lo derrota y por qué?",

  "historical_wins_pattern": "patrón en las victorias — ¿cómo gana? ¿qué tipo de peleador derrota fácil?",

  "matchup_history_vs_similar": "comportamiento vs peleadores con guardia/estilo similar al nuestro",

  "orthodox_vs_southpaw": "comportamiento específico vs orthodox y vs southpaw",

  "clinch_game": "juego de clinch completo — ofensivo y defensivo",

  "ground_game": "juego en suelo si aplica al deporte",

  "summary": "resumen ejecutivo del scouting — 5-6 oraciones que cualquier entrenador entendería inmediatamente"
}}

Responde SOLO con el JSON. Sin markdown, sin explicaciones.
""".strip()


class GeminiEngine(BaseVideoEngine):
    """Motor de análisis de video usando Gemini 2.0 Flash."""

    name = "gemini"
    MODEL = "gemini-2.0-flash"   # ← modelo correcto y estable

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY no configurada")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._model = genai.GenerativeModel(self.MODEL)

    # ── Análisis de una pelea individual ─────────────────────────────────────

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

        # Usar URL de YouTube directamente con Gemini
        if video_source.startswith("http"):
            contents = [prompt, {"video_url": video_source}]
        else:
            # Video local — subir con File API
            import pathlib
            video_file = await asyncio.to_thread(
                genai.upload_file, video_source
            )
            contents = [prompt, video_file]

        response = await asyncio.to_thread(
            self._model.generate_content, contents
        )

        raw = response.text.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        data = json.loads(raw)
        return FightAnalysisResult(**data)

    # ── Síntesis de scouting (TODAS las peleas) ───────────────────────────────

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

        response = await asyncio.to_thread(
            self._model.generate_content, prompt
        )

        raw = response.text.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        data = json.loads(raw)
        return FighterStyleProfile(**data)
