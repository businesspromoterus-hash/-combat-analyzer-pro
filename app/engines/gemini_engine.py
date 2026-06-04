"""
Motor Gemini: análisis enriquecido con datos de internet + video.
Modelo: gemini-2.0-flash

FLUJO:
1. Claude busca en internet todo lo que existe sobre el peleador
2. Gemini recibe el video + esa información como contexto
3. El scouting combina lo visto en video + lo conocido públicamente
"""
import json
import re
import asyncio
import mimetypes
from typing import Optional
import anthropic
import google.generativeai as genai

from app.core.config import settings
from app.engines.base import (
    BaseVideoEngine,
    FightAnalysisResult,
    FighterStyleProfile,
)


def _read_file_bytes(path: str) -> bytes:
    """Lee el contenido binario de un archivo de video subido."""
    with open(path, "rb") as f:
        return f.read()


# ── Prompt de búsqueda web (Claude busca info del peleador) ──────────────────

WEB_RESEARCH_PROMPT = """
Busca información pública sobre el peleador: "{fighter_name}" ({sport}).

Necesito toda la información disponible en internet:
- Estilo de pelea conocido públicamente
- Fortalezas y debilidades mencionadas por expertos y analistas
- Historial de peleas completo — contra quién ganó, contra quién perdió y por qué
- Cambios de entrenador o gimnasio
- Lesiones conocidas
- Lo que el mismo peleador ha dicho en entrevistas sobre su estilo
- Estadísticas públicas (CompuBox, Tapology, Sherdog, etc.)
- Análisis de expertos y comentaristas
- Cualquier información táctica relevante

Sé específico y detallado. Solo incluye información que realmente encontraste.

Responde en formato JSON:
{{
  "fighter_name": "{fighter_name}",
  "sport": "{sport}",
  "public_style_description": "descripción del estilo según fuentes públicas",
  "publicly_known_strengths": ["fortaleza 1 según expertos", "fortaleza 2"],
  "publicly_known_weaknesses": ["debilidad 1 conocida", "debilidad 2"],
  "loss_patterns": "análisis de sus derrotas — qué tipo de peleador lo derrota",
  "win_patterns": "análisis de sus victorias — cómo suele ganar",
  "training_background": "entrenador actual, gimnasio, sistema de entrenamiento",
  "injuries_known": "lesiones conocidas que puedan afectar su rendimiento",
  "fighter_own_words": "lo que el peleador ha dicho sobre su estilo en entrevistas",
  "expert_analysis": "lo que analistas y comentaristas dicen de él",
  "recent_form": "forma reciente — últimas peleas y tendencia",
  "additional_context": "cualquier información adicional relevante",
  "sources_consulted": ["fuente 1", "fuente 2"]
}}

Solo JSON, sin markdown.
""".strip()


# ── Prompt de análisis de video con contexto enriquecido ─────────────────────

ENRICHED_FIGHT_ANALYSIS_PROMPT = """
Eres un analista de deportes de combate de élite con acceso al video completo.

PELEADOR A ANALIZAR: {fighter_name}
DEPORTE: {sport}
{coach_notes_block}

════════════════════════════════════════
CONTEXTO DE INTERNET — LO QUE SE SABE PÚBLICAMENTE:
{web_context}
════════════════════════════════════════

INSTRUCCIÓN CRÍTICA — TIMESTAMPS:
Para CADA observación táctica positiva o negativa DEBES indicar:
- En qué ROUND ocurre
- En qué MINUTO aproximado (ej: "Round 3, min 1:20")
- Si es patrón repetido, menciona TODOS los momentos

INSTRUCCIÓN DE ENRIQUECIMIENTO:
Cuando observes algo en el video, indica si:
- CONFIRMA lo que se sabe públicamente — ej: "Confirma su reputación de buen jab"
- CONTRADICE lo conocido — ej: "Contrario a lo reportado, su cardio se ve sólido en rounds tardíos"
- ES NUEVO — ej: "Nuevo patrón no reportado: usa más el gancho al cuerpo"

Genera el análisis completo en JSON:

{{
  "fighter_name": "{fighter_name}",
  "fight_summary": "resumen de la pelea y resultado",

  "context_validation": {{
    "confirms_public_knowledge": ["observación 1 que confirma lo conocido con timestamp", "observación 2"],
    "contradicts_public_knowledge": ["observación que contradice lo conocido con timestamp"],
    "new_discoveries": ["patrón nuevo no reportado públicamente con timestamp"]
  }},

  "offensive_patterns": {{
    "favorite_strikes": [
      "Técnica — Round X min Y:ZZ — confirma/contradice/nuevo"
    ],
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
      "Error — Round X min Y:ZZ, Round A min B:CC — conocido públicamente / nuevo descubrimiento"
    ],
    "vulnerable_angles": ["ángulo con timestamp"],
    "clinch_defense": "descripción con timestamps",
    "takedown_defense": "descripción con timestamps si aplica"
  }},

  "physical_attributes": {{
    "cardio_assessment": "evaluación con timestamps — compara con reputación pública",
    "power_level": "con timestamps de momentos de poder",
    "chin_durability": "con timestamps de impactos recibidos",
    "speed_assessment": "con timestamps — compara con reputación",
    "strength_in_clinch": "con timestamps"
  }},

  "mental_game": {{
    "pressure_response": "con timestamps — compara con lo conocido públicamente",
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
    "late_rounds": "rounds finales con timestamps — compara con reputación de cardio",
    "rhythm_drops": ["bajón con timestamp y contexto"]
  }},

  "key_moments": [
    {{
      "round": 3,
      "timestamp": "1:45",
      "type": "weakness",
      "description": "descripción del momento",
      "public_context": "esto es conocido públicamente / esto es un nuevo descubrimiento",
      "importance": "alta/media/baja"
    }}
  ],

  "fight_result_analysis": {{
    "result": "ganó/perdió/empate",
    "why_won_or_lost": "análisis con timestamps y contexto público",
    "turning_point": "Round X min Y:ZZ",
    "adjustments_made": "con timestamps"
  }},

  "strengths": [
    "Fortaleza — Round X min Y — confirma reputación pública / nuevo descubrimiento"
  ],

  "weaknesses": [
    "Debilidad — Round X min Y — conocida públicamente / nueva en este video"
  ],

  "intelligence_summary": "resumen combinando lo del video con el contexto de internet — qué confirma, qué contradice, qué es nuevo"
}}

REGLA DE ORO: Cada observación debe tener Round + minuto Y contexto (confirma/contradice/nuevo).

Responde SOLO con el JSON. Sin markdown.
""".strip()


# ── Prompt de síntesis de scouting enriquecido ───────────────────────────────

ENRICHED_SCOUTING_SYNTHESIS_PROMPT = """
Eres el jefe de scouting de un equipo de combate de élite.

Recibes {num_fights} análisis de peleas de {fighter_name} ({sport}).
Cada análisis combina observaciones del video con contexto de internet.

Tu tarea: sintetizar TODO en el reporte de scouting más completo y profesional posible.
Cada patrón debe incluir:
- Timestamps de referencia de múltiples peleas
- Si está confirmado por múltiples fuentes (video + internet)
- Si es un descubrimiento nuevo solo visible en video

DATOS BIO: {bio_data}

ANÁLISIS DE PELEAS:
{analyses_text}

Genera el reporte completo en JSON:

{{
  "fighter_name": "{fighter_name}",
  "sport": "{sport}",
  "fights_reviewed": {num_fights},

  "intelligence_confidence": "alta/media/baja — qué tan confiable es el scouting basado en fuentes disponibles",

  "overall_style": "descripción completa combinando video + fuentes públicas",

  "consistent_strengths": [
    "Fortaleza — confirmada en video (timestamps) + fuentes públicas",
    "mínimo 6 fortalezas con referencias"
  ],

  "consistent_weaknesses": [
    "Debilidad — timestamps de todas las peleas + contexto público",
    "mínimo 6 debilidades"
  ],

  "signature_techniques": [
    "Técnica con timestamps y contexto público",
    "mínimo 5 técnicas"
  ],

  "recurring_defensive_errors": [
    "Error — timestamps múltiples peleas — conocido/nuevo descubrimiento",
    "mínimo 4 errores"
  ],

  "key_moments_across_fights": [
    {{
      "fight": "vs Rival",
      "round": 3,
      "timestamp": "1:45",
      "type": "weakness",
      "description": "descripción",
      "source": "video / video+internet / internet"
    }}
  ],

  "confirmed_by_multiple_sources": [
    "patrón confirmado tanto en video como en fuentes públicas"
  ],

  "new_discoveries_video_only": [
    "patrón nuevo encontrado en video que no está reportado públicamente"
  ],

  "contradictions_found": [
    "algo que contradice su reputación pública — con evidencia del video"
  ],

  "cardio_profile": "evaluación con timestamps y comparación con reputación pública",
  "late_round_behavior": "con timestamps",
  "rhythm_drop_patterns": ["patrón con timestamps de múltiples peleas"],
  "mental_profile": "con timestamps y contexto público",
  "corner_adaptability": "con evidencia de video",
  "strategy_evolution": "con evidencia de video",
  "historical_losses_pattern": "con referencias de video e internet",
  "historical_wins_pattern": "con referencias",
  "matchup_history_vs_similar": "con timestamps y referencias",
  "orthodox_vs_southpaw": "con timestamps",

  "summary": "resumen ejecutivo combinando video + internet — 5-6 oraciones para el entrenador"
}}

Responde SOLO con el JSON. Sin markdown.
""".strip()


class GeminiEngine(BaseVideoEngine):
    """
    Motor Gemini 2.0 Flash con análisis enriquecido.
    Combina análisis de video con datos de internet.
    """

    name = "gemini"
    MODEL = "gemini-2.0-flash"

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY no configurada")
        if not settings.ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY no configurada")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._model = genai.GenerativeModel(self.MODEL)
        self._claude = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def _research_fighter_online(
        self,
        fighter_name: str,
        sport: str,
    ) -> dict:
        """
        Claude busca en internet toda la información pública sobre el peleador.
        """
        prompt = WEB_RESEARCH_PROMPT.format(
            fighter_name=fighter_name,
            sport=sport,
        )

        try:
            response = await asyncio.to_thread(
                self._claude.messages.create,
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
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
            return json.loads(raw)

        except Exception as e:
            # Si falla la búsqueda web, continúa sin contexto de internet
            return {
                "fighter_name": fighter_name,
                "public_style_description": "Sin datos de internet disponibles",
                "note": f"Búsqueda web no disponible: {str(e)}"
            }

    async def analyze_fight_video(
        self,
        video_source: str,
        fighter_name: str,
        sport: str,
        coach_notes: Optional[str] = None,
    ) -> FightAnalysisResult:
        """
        FASE 1: Claude busca info del peleador en internet.
        FASE 2: Gemini analiza el video con ese contexto enriquecido.
        """

        # Fase 1: Buscar info en internet
        web_context = await self._research_fighter_online(fighter_name, sport)

        coach_block = f"\nNOTAS DEL ENTRENADOR: {coach_notes}" if coach_notes else ""

        prompt = ENRICHED_FIGHT_ANALYSIS_PROMPT.format(
            fighter_name=fighter_name,
            sport=sport,
            coach_notes_block=coach_block,
            web_context=json.dumps(web_context, ensure_ascii=False, indent=2),
        )

        # Fase 2: Gemini analiza el video con contexto.
        #
        # Hay dos flujos distintos según el origen del video:
        #
        #  • ENLACE (YouTube u otra URL): Gemini debe MIRAR el video directamente
        #    desde la URL. Se pasa como file_data/file_uri — NO se descarga ni se
        #    convierte a archivo. Gemini accede al video por la URL tal cual.
        #
        #  • ARCHIVO SUBIDO: se envía el contenido binario del video como
        #    inline_data (bytes incrustados en la petición).
        if video_source.startswith("http"):
            video_part = {"file_data": {"file_uri": video_source}}
        else:
            mime_type, _ = mimetypes.guess_type(video_source)
            video_bytes = await asyncio.to_thread(_read_file_bytes, video_source)
            video_part = {
                "inline_data": {
                    "mime_type": mime_type or "video/mp4",
                    "data": video_bytes,
                }
            }

        contents = [prompt, video_part]

        response = await asyncio.to_thread(
            self._model.generate_content, contents
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
        """
        Sintetiza el scouting completo combinando todos los análisis enriquecidos.
        """
        analyses_text = "\n\n".join(
            f"=== PELEA {i+1} ===\n{json.dumps(a.model_dump(), ensure_ascii=False, indent=2)}"
            for i, a in enumerate(individual_analyses)
        )

        prompt = ENRICHED_SCOUTING_SYNTHESIS_PROMPT.format(
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
