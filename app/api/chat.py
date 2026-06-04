"""
Chat contextual enriquecido — Claude responde combinando:
1. Datos internos de FightIQ (scouting, perfiles, planes)
2. Búsqueda en internet en tiempo real
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import anthropic
import json

from app.core.database import get_db
from app.core.config import settings
from app.api.auth import get_current_user
from app.models import db_models as m

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    context_type: str = "general"
    context_id: Optional[int] = None


def build_system_prompt(
    context_type: str,
    db: Session,
    context_id: Optional[int],
    owner_id: Optional[int] = None,
) -> str:
    base = """Eres el asistente táctico de FightIQ.
Eres un experto en deportes de combate: boxeo, MMA, kickboxing, muay thai, judo, BJJ, karate, karate combat, BKFC, taekwondo y lucha.
Respondes como un entrenador de élite — directo, profesional y específico.

INSTRUCCIÓN CRÍTICA:
Combina SIEMPRE dos fuentes de información:
1. Los datos internos de FightIQ (scouting, perfiles, análisis de video con timestamps)
2. Tu conocimiento público y búsquedas en internet en tiempo real

Cuando respondas, indica de dónde viene cada dato:
- "Según el análisis de video en FightIQ (Round 3, min 1:20)..."
- "Según fuentes públicas..."
- "Combinando el video con lo conocido públicamente..."

Si el entrenador pregunta en español, responde en español. Si pregunta en inglés, responde en inglés."""

    if context_type == "fighter" and context_id:
        fq = db.query(m.Fighter).filter(m.Fighter.id == context_id)
        if owner_id is not None:
            fq = fq.filter(m.Fighter.owner_id == owner_id)
        fighter = fq.first()
        if not fighter:
            return base

        fights = fighter.fights or []
        analyses = []
        for fight in fights:
            for a in fight.analyses:
                if a.status == m.AnalysisStatus.COMPLETED and a.result:
                    analyses.append(a.result)

        profile = db.query(m.FighterProfile).filter(
            m.FighterProfile.fighter_id == context_id
        ).first()

        scouting = db.query(m.ScoutingReport).filter(
            m.ScoutingReport.fighter_id == context_id
        ).order_by(m.ScoutingReport.created_at.desc()).first()

        ctx = f"""
CONTEXTO INTERNO DE FIGHTIQ — {fighter.name}:
- Deporte: {fighter.sport.value}
- Guardia: {fighter.stance.value}
- Récord: {fighter.record_str}
- División: {fighter.division or 'N/A'}
- País: {fighter.country or 'N/A'}
- Peleas analizadas en FightIQ: {len(analyses)}
"""
        if scouting:
            ctx += f"\nSCOUTING COMPLETO (video + internet):\n{json.dumps(scouting.report, ensure_ascii=False, indent=2)}"
        elif profile:
            ctx += f"\nPERFIL TÁCTICO:\n{json.dumps(profile.profile, ensure_ascii=False, indent=2)}"

        if analyses:
            ctx += f"\nÚLTIMO ANÁLISIS DE VIDEO:\n{json.dumps(analyses[-1], ensure_ascii=False, indent=2)}"

        return base + ctx + f"\n\nAdemás de estos datos internos, busca en internet información adicional sobre {fighter.name} cuando sea relevante para responder."

    if context_type == "scouting" and context_id:
        scouting = db.query(m.ScoutingReport).filter(
            m.ScoutingReport.id == context_id
        ).first()
        if not scouting:
            return base

        fighter = db.query(m.Fighter).filter(
            m.Fighter.id == scouting.fighter_id
        ).first()
        if owner_id is not None and (not fighter or fighter.owner_id != owner_id):
            return base

        ctx = f"""
CONTEXTO INTERNO — SCOUTING DE {fighter.name if fighter else 'peleador'}:
{json.dumps(scouting.report, ensure_ascii=False, indent=2)}
"""
        return base + ctx + f"\n\nCombina este scouting con información pública adicional de internet sobre {fighter.name if fighter else 'el peleador'} cuando sea relevante."

    if context_type == "plan" and context_id:
        plan = db.query(m.FightPlan).filter(m.FightPlan.id == context_id).first()
        if not plan:
            return base

        our = db.query(m.Fighter).filter(m.Fighter.id == plan.our_fighter_id).first()
        if owner_id is not None and (not our or our.owner_id != owner_id):
            return base
        opp = db.query(m.Fighter).filter(m.Fighter.id == plan.opponent_id).first()

        our_scouting = db.query(m.ScoutingReport).filter(
            m.ScoutingReport.fighter_id == plan.our_fighter_id
        ).order_by(m.ScoutingReport.created_at.desc()).first()

        opp_scouting = db.query(m.ScoutingReport).filter(
            m.ScoutingReport.fighter_id == plan.opponent_id
        ).order_by(m.ScoutingReport.created_at.desc()).first()

        ctx = f"""
CONTEXTO INTERNO — PLAN DE COMBATE:
NUESTRO PELEADOR: {our.name if our else 'N/A'}
RIVAL: {opp.name if opp else 'N/A'}

PLAN COMPLETO:
{json.dumps(plan.plan, ensure_ascii=False, indent=2)}
"""
        if our_scouting:
            ctx += f"\nSCOUTING NUESTRO PELEADOR:\n{json.dumps(our_scouting.report, ensure_ascii=False, indent=2)}"
        if opp_scouting:
            ctx += f"\nSCOUTING RIVAL:\n{json.dumps(opp_scouting.report, ensure_ascii=False, indent=2)}"

        names = f"{our.name if our else ''} y {opp.name if opp else ''}"
        return base + ctx + f"\n\nCombina estos datos con información pública de internet sobre {names} cuando sea relevante para responder."

    return base + "\n\nBusca en internet cuando el entrenador pregunte sobre peleadores, tácticas o información específica."


@router.post("/")
async def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    user: m.User = Depends(get_current_user),
):
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(500, "ANTHROPIC_API_KEY no configurada")

    system = build_system_prompt(
        context_type=req.context_type,
        db=db,
        context_id=req.context_id,
        owner_id=user.id,
    )

    messages = []
    for msg in req.history[-10:]:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": req.message})

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def generate():
        with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=system,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                import json as _json
                yield f"data: {_json.dumps({'text': text})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )
