"""
Motor Claude (Anthropic) - especializado en ESTRATEGIA y razonamiento táctico.

Claude no procesa video nativamente, pero es excelente para:
- Sintetizar perfiles a partir de análisis individuales
- Generar planes de combate complejos
- Razonamiento multi-paso (plan rival → contramedidas → sparrings)
"""
import json
import asyncio
from typing import Optional
from anthropic import Anthropic

from app.core.config import settings
from app.engines.base import (
    AIEngine, FightAnalysisResult, FighterStyleProfile, CompleteFightPlan
)
from app.engines.prompts import (
    SPORT_VOCABULARY, FIGHT_ANALYSIS_PROMPT,
    PROFILE_SYNTHESIS_PROMPT, FIGHT_PLAN_PROMPT
)


class ClaudeEngine(AIEngine):
    name = "claude"
    supports_video = False        # texto/notas, no video nativo
    supports_strategy = True
    supports_vision = False        # Claude tiene vision pero no para video largo

    def __init__(self, model_name: str = "claude-opus-4-7"):
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY no configurada en .env")
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model_name = model_name

    @staticmethod
    def _strip_json(raw: str) -> dict:
        s = raw.strip()
        if s.startswith("```"):
            s = "\n".join(s.split("\n")[1:-1])
        # buscar primer { y último }
        start = s.find("{")
        end = s.rfind("}")
        if start >= 0 and end > start:
            s = s[start:end + 1]
        return json.loads(s)

    async def _complete(self, prompt: str, max_tokens: int = 4096) -> str:
        loop = asyncio.get_event_loop()
        msg = await loop.run_in_executor(
            None,
            lambda: self.client.messages.create(
                model=self.model_name,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            ),
        )
        return msg.content[0].text

    async def analyze_fight_video(
        self,
        video_source: str,
        fighter_name: str,
        sport: str,
        coach_notes: Optional[str] = None,
    ) -> FightAnalysisResult:
        """
        Claude no procesa video, así que usa SOLO las notas del coach + metadata.
        Para video real usar Gemini. Esto sirve como fallback o complemento.
        """
        vocab = SPORT_VOCABULARY.get(sport, SPORT_VOCABULARY["other"])
        prompt = FIGHT_ANALYSIS_PROMPT.format(
            fighter_name=fighter_name,
            sport=sport,
            vocab=vocab,
            coach_notes=coach_notes or "Sin notas. Análisis basado solo en metadata limitada.",
        )
        prompt += "\n\nNOTA: No tienes acceso al video, solo a las notas del entrenador y metadata. Marca confidence bajo (0.3-0.5) y sé honesto sobre limitaciones."

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
        return CompleteFightPlan(**self._strip_json(raw))
