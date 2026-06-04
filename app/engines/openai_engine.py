"""
Motor OpenAI (GPT-4o) - vision pero no video nativo de largo plazo.

Útil para:
- Análisis de frames clave (imágenes extraídas del video)
- Síntesis y planes de combate
- Backup si Gemini falla
"""
import json
import asyncio
from typing import Optional
from openai import OpenAI

from app.core.config import settings
from app.engines.base import (
    AIEngine, FightAnalysisResult, FighterStyleProfile, CompleteFightPlan
)
from app.engines.prompts import (
    SPORT_VOCABULARY, FIGHT_ANALYSIS_PROMPT,
    PROFILE_SYNTHESIS_PROMPT, FIGHT_PLAN_PROMPT
)
from app.engines.normalize import coerce_fight_plan


class OpenAIEngine(AIEngine):
    name = "openai"
    supports_video = False
    supports_strategy = True
    supports_vision = True   # imágenes/frames sí

    def __init__(self, model_name: str = "gpt-4o"):
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY no configurada en .env")
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model_name = model_name

    @staticmethod
    def _strip_json(raw: str) -> dict:
        s = raw.strip()
        if s.startswith("```"):
            s = "\n".join(s.split("\n")[1:-1])
        start = s.find("{")
        end = s.rfind("}")
        if start >= 0 and end > start:
            s = s[start:end + 1]
        return json.loads(s)

    async def _complete(self, prompt: str, max_tokens: int = 4096) -> str:
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(
            None,
            lambda: self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            ),
        )
        return resp.choices[0].message.content

    async def analyze_fight_video(
        self,
        video_source: str,
        fighter_name: str,
        sport: str,
        coach_notes: Optional[str] = None,
    ) -> FightAnalysisResult:
        # OpenAI no procesa video largo: fallback a notas + metadata
        vocab = SPORT_VOCABULARY.get(sport, SPORT_VOCABULARY["other"])
        prompt = FIGHT_ANALYSIS_PROMPT.format(
            fighter_name=fighter_name,
            sport=sport,
            vocab=vocab,
            coach_notes=coach_notes or "Sin notas del entrenador.",
        )
        prompt += "\n\nNOTA: Análisis basado en notas + metadata. confidence: 0.3-0.5."
        raw = await self._complete(prompt, max_tokens=3000)
        return FightAnalysisResult(**self._strip_json(raw))

    async def synthesize_fighter_profile(
        self,
        fighter_name: str,
        sport: str,
        individual_analyses: list[FightAnalysisResult],
        bio_data: dict,
    ) -> FighterStyleProfile:
        prompt = PROFILE_SYNTHESIS_PROMPT.format(
            fighter_name=fighter_name,
            sport=sport,
            bio_data=json.dumps(bio_data, ensure_ascii=False),
            num_analyses=len(individual_analyses),
            analyses_json=json.dumps(
                [a.model_dump() for a in individual_analyses], ensure_ascii=False
            ),
        )
        raw = await self._complete(prompt, max_tokens=3000)
        return FighterStyleProfile(**self._strip_json(raw))

    async def generate_fight_plan(
        self,
        our_profile: FighterStyleProfile,
        our_bio: dict,
        opponent_profile: FighterStyleProfile,
        opponent_bio: dict,
        sport: str,
        additional_context: Optional[str] = None,
    ) -> CompleteFightPlan:
        vocab = SPORT_VOCABULARY.get(sport, SPORT_VOCABULARY["other"])
        prompt = FIGHT_PLAN_PROMPT.format(
            sport=sport,
            vocab=vocab,
            our_bio=json.dumps(our_bio, ensure_ascii=False),
            our_profile=json.dumps(our_profile.model_dump(), ensure_ascii=False),
            opponent_bio=json.dumps(opponent_bio, ensure_ascii=False),
            opponent_profile=json.dumps(opponent_profile.model_dump(), ensure_ascii=False),
            additional_context=additional_context or "ninguno",
        )
        raw = await self._complete(prompt, max_tokens=8000)
        return CompleteFightPlan(**coerce_fight_plan(self._strip_json(raw)))
