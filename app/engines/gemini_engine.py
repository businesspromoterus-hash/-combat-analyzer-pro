"""
Motor Gemini para análisis REAL de video de peleas.

Gemini 1.5/2.0 puede procesar video nativamente vía:
1. File API (subir archivo local)
2. YouTube URL directa (Gemini 2.0+)
"""
import json
import asyncio
from typing import Optional
import google.generativeai as genai

from app.core.config import settings
from app.engines.base import (
    AIEngine, FightAnalysisResult, FighterStyleProfile, CompleteFightPlan
)
from app.engines.prompts import (
    SPORT_VOCABULARY, FIGHT_ANALYSIS_PROMPT,
    PROFILE_SYNTHESIS_PROMPT, FIGHT_PLAN_PROMPT
)


class GeminiEngine(AIEngine):
    name = "gemini"
    supports_video = True
    supports_strategy = True
    supports_vision = True

    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY no configurada en .env")
        genai.configure(api_key=settings.gemini_api_key)
        self.model_name = model_name
        self.model = genai.GenerativeModel(
            model_name,
            generation_config={
                "temperature": 0.4,
                "response_mime_type": "application/json",
            },
        )

    # ---------- helpers ----------

    @staticmethod
    def _strip_json(raw: str) -> dict:
        """Limpia salida y parsea JSON, robusto a fences markdown."""
        s = raw.strip()
        if s.startswith("```"):
            # quita primera línea (```json) y última (```)
            s = "\n".join(s.split("\n")[1:-1])
        return json.loads(s)

    async def _upload_video_file(self, file_path: str):
        """Sube archivo de video a Gemini File API y espera a que esté listo."""
        loop = asyncio.get_event_loop()
        uploaded = await loop.run_in_executor(None, genai.upload_file, file_path)
        # Esperar a que termine de procesar
        for _ in range(60):    # hasta 5 min
            uploaded = await loop.run_in_executor(None, genai.get_file, uploaded.name)
            if uploaded.state.name == "ACTIVE":
                return uploaded
            if uploaded.state.name == "FAILED":
                raise RuntimeError(f"Gemini falló procesando el video: {uploaded.name}")
            await asyncio.sleep(5)
        raise TimeoutError("Gemini tardó demasiado procesando el video")

    # ---------- API pública ----------

    async def analyze_fight_video(
        self,
        video_source: str,
        fighter_name: str,
        sport: str,
        coach_notes: Optional[str] = None,
    ) -> FightAnalysisResult:
        vocab = SPORT_VOCABULARY.get(sport, SPORT_VOCABULARY["other"])
        prompt = FIGHT_ANALYSIS_PROMPT.format(
            fighter_name=fighter_name,
            sport=sport,
            vocab=vocab,
            coach_notes=coach_notes or "ninguna",
        )

        # Construir contenido (video + prompt)
        if video_source.startswith("http"):
            # YouTube URL directa (Gemini 2.0+)
            content = [
                {"file_data": {"file_uri": video_source, "mime_type": "video/mp4"}},
                prompt,
            ]
        else:
            # Archivo local: subir a File API
            uploaded = await self._upload_video_file(video_source)
            content = [uploaded, prompt]

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: self.model.generate_content(content)
        )

        data = self._strip_json(response.text)
        return FightAnalysisResult(**data)

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

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: self.model.generate_content(prompt)
        )
        return FighterStyleProfile(**self._strip_json(response.text))

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

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: self.model.generate_content(prompt)
        )
        return CompleteFightPlan(**self._strip_json(response.text))
