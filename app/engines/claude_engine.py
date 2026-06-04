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
from app.engines.prompts import SPORT_VOCABULARY, FIGHT_PLAN_PROMPT
from app.engines.normalize import coerce_fight_plan


FIGHT_PREDICTION_PROMPT = """
Eres un analista experto de deportes de combate. Predice el resultado más probable
de la pelea entre estos dos peleadores, combinando los datos internos con lo que
encuentres en internet sobre su forma reciente.

DEPORTE: {sport}

PELEADOR A (NUESTRO):
{our_bio}
{our_context}

PELEADOR B (RIVAL):
{opp_bio}
{opp_context}

Devuelve SOLO este JSON (sin markdown):
{{
  "winner": "nombre del peleador que probablemente gana",
  "confidence_percentage": 65,
  "method": "KO/TKO, Sumisión, Decisión unánime, Decisión dividida o Puntos",
  "estimated_round": "ronda estimada del desenlace (ej: 'Round 7') o 'Decisión (a la distancia)'",
  "reasoning": "explicación clara en 3-5 oraciones basada en estilos, récord y forma",
  "key_factors": ["factor decisivo 1", "factor 2", "factor 3"]
}}
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

    async def predict_fight(
        self,
        our_bio: dict,
        opponent_bio: dict,
        sport: str,
        our_context: Optional[dict] = None,
        opponent_context: Optional[dict] = None,
    ) -> dict:
        def _ctx(label, data):
            return f"\n{label}:\n{json.dumps(data, ensure_ascii=False, indent=2)}" if data else ""

        prompt = FIGHT_PREDICTION_PROMPT.format(
            sport=sport,
            our_bio=json.dumps(our_bio, ensure_ascii=False, indent=2),
            opp_bio=json.dumps(opponent_bio, ensure_ascii=False, indent=2),
            our_context=_ctx("SCOUTING NUESTRO", our_context),
            opp_context=_ctx("SCOUTING RIVAL", opponent_context),
        )

        response = await asyncio.to_thread(
            self._client.messages.create,
            model=self.MODEL,
            max_tokens=1500,
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

    async def generate_fight_plan(
        self,
        our_profile: FighterStyleProfile,
        our_bio: dict,
        opponent_profile: FighterStyleProfile,
        opponent_bio: dict,
        sport: str,
        additional_context: Optional[str] = None,
    ) -> CompleteFightPlan:

        # Usamos el prompt COMPARTIDO (prompts.FIGHT_PLAN_PROMPT), alineado con
        # el esquema CompleteFightPlan y con lo que renderiza la UI/PDF. Antes
        # este motor tenía un prompt local con una estructura JSON distinta, lo
        # que provocaba ValidationError al construir CompleteFightPlan.
        vocab = SPORT_VOCABULARY.get(sport, SPORT_VOCABULARY["other"])
        prompt = FIGHT_PLAN_PROMPT.format(
            sport=sport,
            vocab=vocab,
            our_bio=json.dumps(our_bio, ensure_ascii=False, indent=2),
            our_profile=json.dumps(our_profile.model_dump(), ensure_ascii=False, indent=2),
            opponent_bio=json.dumps(opponent_bio, ensure_ascii=False, indent=2),
            opponent_profile=json.dumps(opponent_profile.model_dump(), ensure_ascii=False, indent=2),
            additional_context=additional_context or "ninguno",
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
        # Con web_search, Claude suele anteponer texto/citas al JSON; extraer el
        # objeto balanceado antes de parsear y normalizar para evitar errores.
        if not raw.lstrip().startswith("{"):
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                raw = match.group(0)
        data = coerce_fight_plan(json.loads(raw))
        return CompleteFightPlan(**data)
