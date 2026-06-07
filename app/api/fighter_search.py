"""
API de búsqueda automática de peleadores.
El entrenador escribe el nombre y Gemini busca los datos automáticamente en
internet. Si no encuentra nada, el entrenador puede meter todo a mano.
"""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import google.generativeai as genai
import json
import re

from app.core.database import get_db
from app.core.config import settings
from app.api.auth import get_current_user
from app.models import db_models as m

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fighters/search", tags=["fighter-search"])

GEMINI_SEARCH_MODEL = "gemini-2.5-flash"


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
    years_experience_pro: Optional[int] = None
    years_experience_amateur: Optional[int] = None
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
async def search_fighter(
    req: FighterSearchRequest,
    user: m.User = Depends(get_current_user),
):
    """
    Busca datos de un peleador por nombre.
    Usa Gemini con búsqueda en Google para encontrar información pública.
    Retorna hasta 3 posibles coincidencias para que el entrenador elija.
    Si no encuentra nada, retorna found=False para que el entrenador meta datos manuales.
    """
    if not settings.GEMINI_API_KEY:
        # No exponemos detalle técnico; el entrenador puede ingresar a mano.
        return FighterSearchResponse(
            results=[],
            found=False,
            message="La búsqueda automática no está disponible ahora. Ingresa los datos manualmente.",
        )

    sport_context = f"Deporte: {req.sport}." if req.sport else "Puede ser cualquier deporte de combate."

    prompt = f"""
Busca información sobre el peleador: "{req.name}"
{sport_context}

Busca en internet datos reales y actuales sobre este peleador de combate.
Puede ser boxeador, peleador de MMA, kickboxer, judoka, etc.

CÓMO BUSCAR (importante para encontrar también a peleadores menos mediáticos):
- Consulta BoxRec, Tapology, Sherdog, Wikipedia, ESPN y federaciones olímpicas/amateur.
- Considera variantes del nombre: con y sin acentos/tildes, orden de apellidos,
  diminutivos y la grafía en inglés (ej: "Robeisy Ramírez" = "Robeisy Ramirez",
  medallista olímpico cubano de boxeo, también buscado como "Robeisy Carrillo").
- Incluye a peleadores con trayectoria amateur/olímpica relevante aunque su
  carrera profesional sea corta o reciente.
- Si hay coincidencia razonable, devuélvela aunque la confianza sea media.

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
      "years_experience_pro": null,
      "years_experience_amateur": null,
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

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_SEARCH_MODEL)

    def _generate() -> str:
        """
        Llama a Gemini pidiéndole que busque en internet. Intenta primero con la
        herramienta de Google Search (grounding); si el SDK/modelo no la acepta,
        cae a una generación normal con el conocimiento del propio modelo.
        """
        try:
            resp = model.generate_content(prompt, tools=[{"google_search": {}}])
        except Exception:
            resp = model.generate_content(prompt)
        return (resp.text or "")

    try:
        raw = _generate()

        raw = raw.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        # Con la herramienta de web_search, el modelo suele anteponer texto,
        # citas o explicaciones antes/después del JSON. Si parseamos el bloque
        # completo, json.loads falla y devolvíamos "no encontrado" incluso para
        # peleadores conocidos (Canelo, Robeisy, etc.). Extraemos el objeto JSON
        # balanceado del texto antes de parsear.
        if not raw.lstrip().startswith("{"):
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                raw = match.group(0)

        data = json.loads(raw)
        return FighterSearchResponse(**data)

    except json.JSONDecodeError:
        return FighterSearchResponse(
            results=[],
            found=False,
            message="No se pudo procesar la búsqueda. Ingresa los datos manualmente."
        )
    except Exception:
        logger.exception("Error en la búsqueda automática de peleador '%s'", req.name)
        return FighterSearchResponse(
            results=[],
            found=False,
            message="No se pudo completar la búsqueda. Ingresa los datos manualmente."
        )
