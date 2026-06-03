"""
API de búsqueda automática de peleadores.
El entrenador escribe el nombre y la app busca los datos automáticamente.
Si no encuentra nada, el entrenador puede meter todo a mano.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import anthropic
import json
import re

from app.core.database import get_db
from app.core.config import settings

router = APIRouter(prefix="/api/fighters/search", tags=["fighter-search"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class FighterSearchResult(BaseModel):
    name: str
    sport: Optional[str] = None
    country: Optional[str] = None
    age: Optional[int] = None
    weight_kg: Optional[float] = None
    division: Optional[str] = None
    height_cm: Optional[float] = None
    reach_cm: Optional[float] = None
    stance: Optional[str] = None
    wins: Optional[int] = None
    losses: Optional[int] = None
    draws: Optional[int] = None
    ko_wins: Optional[int] = None
    sub_wins: Optional[int] = None
    years_experience: Optional[int] = None
    style_summary: Optional[str] = None
    known_strengths: Optional[List[str]] = None
    known_weaknesses: Optional[List[str]] = None
    notable_fights: Optional[List[str]] = None
    current_trainer: Optional[str] = None
    gym: Optional[str] = None
    confidence: float = 0.0  # 0-1, qué tan seguro está de los datos
    source_notes: Optional[str] = None


class FighterSearchRequest(BaseModel):
    name: str
    sport: Optional[str] = None  # Si el entrenador ya sabe el deporte


class FighterSearchResponse(BaseModel):
    results: List[FighterSearchResult]
    found: bool
    message: str


# ── Endpoint de búsqueda ──────────────────────────────────────────────────────

@router.post("/", response_model=FighterSearchResponse)
async def search_fighter(req: FighterSearchRequest):
    """
    Busca datos de un peleador por nombre.
    Usa Claude con web search para encontrar información pública.
    Retorna hasta 3 posibles coincidencias para que el entrenador elija.
    Si no encuentra nada, retorna found=False para que el entrenador meta datos manuales.
    """
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(500, "ANTHROPIC_API_KEY no configurada")

    sport_context = f"Deporte: {req.sport}." if req.sport else "Puede ser cualquier deporte de combate."

    prompt = f"""
Busca información sobre el peleador: "{req.name}"
{sport_context}

Busca en internet datos reales y actuales sobre este peleador de combate.
Puede ser boxeador, peleador de MMA, kickboxer, judoka, etc.

Si encuentras al peleador, devuelve sus datos.
Si hay varios peleadores con nombre similar, devuelve hasta 3 opciones para que el entrenador elija.
Si no encuentras información confiable, devuelve una lista vacía.

IMPORTANTE: Solo incluye datos que realmente encontraste. No inventes ni supongas.
Si no sabes un dato, ponlo como null.

Responde SOLO con este JSON, sin markdown:

{{
  "results": [
    {{
      "name": "nombre completo oficial",
      "sport": "boxing/mma/kickboxing/muay_thai/bjj/judo/karate/taekwondo/wrestling/other",
      "country": "país",
      "age": null,
      "weight_kg": null,
      "division": "división o categoría de peso",
      "height_cm": null,
      "reach_cm": null,
      "stance": "orthodox/southpaw/switch/na",
      "wins": null,
      "losses": null,
      "draws": null,
      "ko_wins": null,
      "sub_wins": null,
      "years_experience": null,
      "style_summary": "descripción del estilo de pelea en 2-3 oraciones",
      "known_strengths": ["fortaleza 1", "fortaleza 2"],
      "known_weaknesses": ["debilidad 1 si es conocida públicamente"],
      "notable_fights": ["vs Rival1 (resultado)", "vs Rival2 (resultado)"],
      "current_trainer": "entrenador actual si se conoce",
      "gym": "gimnasio actual si se conoce",
      "confidence": 0.9,
      "source_notes": "de dónde vienen estos datos — BoxRec, Wikipedia, ESPN, etc."
    }}
  ],
  "found": true,
  "message": "Encontré 1 peleador con ese nombre"
}}

Si no encuentras nada confiable:
{{
  "results": [],
  "found": false,
  "message": "No encontré información sobre este peleador. Puedes ingresar los datos manualmente."
}}
""".strip()

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": prompt}],
        )

        # Extraer el texto de la respuesta
        raw = ""
        for block in response.content:
            if hasattr(block, "text"):
                raw += block.text

        raw = raw.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        data = json.loads(raw)
        return FighterSearchResponse(**data)

    except json.JSONDecodeError:
        return FighterSearchResponse(
            results=[],
            found=False,
            message="No se pudo procesar la búsqueda. Ingresa los datos manualmente."
        )
    except Exception as e:
        return FighterSearchResponse(
            results=[],
            found=False,
            message=f"Error en la búsqueda. Ingresa los datos manualmente."
        )
