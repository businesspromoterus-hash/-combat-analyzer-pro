"""
Normalización defensiva de la salida JSON de los motores de IA.

Los modelos a veces omiten campos requeridos, devuelven el tipo equivocado
(p. ej. un string donde el esquema espera una lista) o anteponen texto al JSON.
Estas funciones garantizan que el dict resultante sea construible por el modelo
Pydantic correspondiente sin lanzar ValidationError.
"""
import re
import json
from typing import Optional


def extract_json_object(raw: str) -> str:
    """
    Devuelve el primer objeto JSON balanceado dentro de `raw`.

    Quita fences de markdown y cualquier texto/citas que el modelo anteponga
    o agregue alrededor del JSON (típico cuando se usa la herramienta de
    búsqueda web). Si no encuentra un objeto, devuelve el texto tal cual.
    """
    s = (raw or "").strip()
    s = re.sub(r"^```json\s*", "", s)
    s = re.sub(r"^```\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    if not s.lstrip().startswith("{"):
        match = re.search(r"\{.*\}", s, re.DOTALL)
        if match:
            s = match.group(0)
    return s


def loads_lenient(raw: str) -> dict:
    """Parsea JSON tolerando texto alrededor del objeto."""
    return json.loads(extract_json_object(raw))


# ── CompleteFightPlan ────────────────────────────────────────────────────────
# Campos REQUERIDOS por el esquema (sin valor por defecto), agrupados por tipo.

_PLAN_DICT_FIELDS = (
    "style_matchup",
    "physical_matchup",
    "plan_a",
    "plan_b",
    "plan_c",
    "opponent_likely_plan",
    "camp_plan",
)
_PLAN_STR_FIELDS = (
    "when_to_press",
    "when_to_exit",
    "when_to_clinch",
    "attack_approach",
    "defense_approach",
    "executive_summary",
)
_PLAN_LIST_STR_FIELDS = (
    "tactical_advantages",
    "tactical_risks",
    "recommended_techniques",
    "techniques_to_avoid",
)
_PLAN_LIST_DICT_FIELDS = (
    "rounds_strategy",
    "countermeasures",
    "sparring_profiles",
)


def coerce_fight_plan(data: dict) -> dict:
    """
    Garantiza que `data` sea válido para CompleteFightPlan.

    - dicts requeridos -> {} si faltan o no son dict
    - strings requeridos -> "No determinado" si faltan o están vacíos
    - listas de strings -> [] / [str(...)] según corresponda
    - listas de dicts -> solo conserva los elementos que son dict
    """
    data = dict(data or {})

    for field in _PLAN_DICT_FIELDS:
        if not isinstance(data.get(field), dict):
            data[field] = {}

    for field in _PLAN_STR_FIELDS:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            data[field] = "No determinado"

    for field in _PLAN_LIST_STR_FIELDS:
        value = data.get(field)
        if isinstance(value, list):
            data[field] = [str(v) for v in value]
        elif value in (None, ""):
            data[field] = []
        else:
            data[field] = [str(value)]

    for field in _PLAN_LIST_DICT_FIELDS:
        value = data.get(field)
        data[field] = [v for v in value if isinstance(v, dict)] if isinstance(value, list) else []

    return data
