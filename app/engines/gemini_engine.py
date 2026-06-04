"""
Motor Gemini: análisis enriquecido con datos de internet + video.
Modelo: gemini-2.5-flash

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
from app.engines.normalize import coerce_analysis, coerce_profile


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

Genera el análisis completo en JSON con EXACTAMENTE estas claves
(no renombres, no anides, no agregues claves nuevas):

{{
  "fighter_name": "{fighter_name}",
  "sport": "{sport}",
  "fighting_style": "estilo de pelea observado en el video, con contexto público",
  "primary_stance_behavior": "guardia/postura principal (orthodox/southpaw/switch) y cómo la usa",
  "strengths": [
    "Fortaleza — Round X min Y:ZZ — confirma reputación pública / nuevo descubrimiento"
  ],
  "weaknesses": [
    "Debilidad — Round X min Y:ZZ — conocida públicamente / nueva en este video"
  ],
  "repeated_patterns": [
    "Patrón repetido — TODOS los Round X min Y:ZZ donde ocurre"
  ],
  "favorite_techniques": [
    "Técnica/golpe favorito — Round X min Y:ZZ — confirma/contradice/nuevo"
  ],
  "defensive_errors": [
    "Error defensivo — Round X min Y:ZZ (y otros momentos) — conocido / nuevo"
  ],
  "when_hand_drops": "cuándo y en qué momentos baja la mano (timestamps), o null",
  "cardio_assessment": "evaluación del cardio con timestamps — compara con reputación pública",
  "pressure_response": "cómo responde a la presión, con timestamps — compara con lo conocido",
  "late_rounds_behavior": "comportamiento en rounds finales con timestamps — compara con reputación de cardio",
  "fatigue_signs": "señales visibles de cansancio con timestamps, o null",
  "mental_state": "estado mental durante la pelea, o null",
  "vs_orthodox": "comportamiento frente a diestros con timestamps, o null",
  "vs_southpaw": "comportamiento frente a zurdos con timestamps, o null",
  "shots_received_most": ["qué golpes/técnicas le conectan más, con timestamps"],
  "movement_pattern": "cómo se mueve (footwork, ángulos) con timestamps, o null",
  "defense_style": "sistema defensivo principal (head movement, guardia, etc.), o null",
  "corner_instructions": "instrucciones de la esquina y ajustes visibles, o null",
  "between_rounds_adjustments": "qué ajusta o no entre rounds, o null",
  "win_loss_cause": "por qué ganó o perdió esta pelea, con timestamps y contexto público",
  "key_moments": [
    {{
      "round": 3,
      "timestamp": "1:45",
      "type": "weakness",
      "description": "descripción del momento",
      "importance": "alta/media/baja"
    }}
  ],
  "danger_signs": ["señal de peligro detectada con timestamp"],
  "confidence": 0.8,
  "notes": "resumen ejecutivo combinando el video con el contexto de internet — qué confirma, qué contradice, qué es nuevo"
}}

REGLA DE ORO: Cada observación debe tener Round + minuto Y contexto (confirma/contradice/nuevo).
Los campos de texto REQUERIDOS (fighting_style, primary_stance_behavior, cardio_assessment,
pressure_response, late_rounds_behavior) NUNCA pueden quedar vacíos. Las listas REQUERIDAS
(strengths, weaknesses, repeated_patterns, favorite_techniques, defensive_errors) deben tener
al menos un elemento.

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

Genera el reporte de scouting en JSON con EXACTAMENTE estas claves
(no renombres, no anides, no agregues claves nuevas):

{{
  "fighter_name": "{fighter_name}",
  "overall_style": "estilo general completo combinando video + fuentes públicas",
  "consistent_strengths": [
    "Fortaleza — confirmada en video (timestamps de varias peleas) + fuentes públicas (mínimo 6)"
  ],
  "consistent_weaknesses": [
    "Debilidad — timestamps de todas las peleas + contexto público (mínimo 6)"
  ],
  "signature_techniques": [
    "Técnica distintiva con timestamps y contexto público (mínimo 5)"
  ],
  "recurring_defensive_holes": [
    "Hueco defensivo recurrente — timestamps de múltiples peleas — conocido/nuevo (mínimo 4)"
  ],
  "cardio_profile": "evaluación del cardio con timestamps y comparación con reputación pública",
  "mental_profile": "respuesta a presión y adversidad, con timestamps y contexto público",
  "historical_losses_pattern": "cómo ha perdido históricamente — referencias de video e internet",
  "matchup_history_vs_similar": "rendimiento frente a peleadores de perfil similar al nuestro, con timestamps y referencias",
  "summary": "resumen ejecutivo combinando video + internet — 5-6 oraciones para el entrenador"
}}

Los campos de texto REQUERIDOS (overall_style, cardio_profile, mental_profile,
historical_losses_pattern, matchup_history_vs_similar, summary) NUNCA pueden quedar vacíos.
Las listas REQUERIDAS (consistent_strengths, consistent_weaknesses, signature_techniques,
recurring_defensive_holes) deben tener al menos un elemento.

Responde SOLO con el JSON. Sin markdown.
""".strip()


class GeminiEngine(BaseVideoEngine):
    """
    Motor Gemini 2.0 Flash con análisis enriquecido.
    Combina análisis de video con datos de internet.
    """

    name = "gemini"
    MODEL = "gemini-2.5-flash"

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
        # Gemini a veces antepone texto al JSON; extraer el objeto balanceado.
        if not raw.lstrip().startswith("{"):
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                raw = match.group(0)
        data = json.loads(raw)
        data = coerce_analysis(data, fighter_name, sport)
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
        # Gemini a veces antepone texto al JSON; extraer el objeto balanceado.
        if not raw.lstrip().startswith("{"):
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                raw = match.group(0)
        data = json.loads(raw)
        data = coerce_profile(data, fighter_name)
        return FighterStyleProfile(**data)
