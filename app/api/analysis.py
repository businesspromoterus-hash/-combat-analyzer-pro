"""Endpoints de análisis IA: pelea, scouting completo, perfil y plan."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models import db_models as m
from app.models import schemas as s
from app.services import analysis_service, fighter_service, fight_service
from app.utils.pdf_generator import generate_pdf_for_plan
from app.engines import list_available_engines


router = APIRouter(prefix="/api/analysis", tags=["analysis"])


def _own_fighter(db: Session, fighter_id: int, user: m.User) -> m.Fighter:
    f = fighter_service.get_fighter(db, fighter_id, owner_id=user.id)
    if not f:
        raise HTTPException(404, "Peleador no encontrado")
    return f


def _own_fight(db: Session, fight_id: int, user: m.User) -> m.Fight:
    f = fight_service.get_owned_fight(db, fight_id, owner_id=user.id)
    if not f:
        raise HTTPException(404, "Pelea no encontrada")
    return f


def _own_plan(db: Session, plan_id: int, user: m.User) -> m.FightPlan:
    plan = db.query(m.FightPlan).filter(m.FightPlan.id == plan_id).first()
    if not plan or not fighter_service.get_fighter(db, plan.our_fighter_id, owner_id=user.id):
        raise HTTPException(404, "Plan no encontrado")
    return plan


@router.get("/engines")
def get_engines(user: m.User = Depends(get_current_user)):
    """Lista motores disponibles y cuáles están configurados."""
    return {"engines": list_available_engines()}


# ========== ANÁLISIS DE PELEA INDIVIDUAL ==========

@router.post("/fight", response_model=s.AnalysisOut)
async def analyze_fight(
    req: s.AnalysisRequest,
    db: Session = Depends(get_db),
    user: m.User = Depends(get_current_user),
):
    """
    Analiza una pelea individual con Gemini.
    Operación síncrona: devuelve cuando termina (puede tardar minutos).
    """
    _own_fight(db, req.fight_id, user)
    try:
        analysis = await analysis_service.analyze_fight(db, req.fight_id, req.engine)
        return analysis
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"{type(e).__name__}: {e}")


@router.get("/fight/{fight_id}", response_model=list[s.AnalysisOut])
def get_fight_analyses(
    fight_id: int,
    db: Session = Depends(get_db),
    user: m.User = Depends(get_current_user),
):
    _own_fight(db, fight_id, user)
    return (
        db.query(m.FightAnalysis)
        .filter(m.FightAnalysis.fight_id == fight_id)
        .order_by(m.FightAnalysis.created_at.desc())
        .all()
    )


# ========== SCOUTING COMPLETO (NUEVO) ==========

@router.post("/scouting/{fighter_id}", response_model=s.ScoutingReportOut)
async def generate_scouting(
    fighter_id: int,
    db: Session = Depends(get_db),
    user: m.User = Depends(get_current_user),
):
    """
    FASE 1: Gemini analiza TODAS las peleas del peleador y genera
    un reporte de scouting profesional completo.

    Este reporte debe revisarse y confirmarse ANTES de generar el plan.
    """
    _own_fighter(db, fighter_id, user)
    try:
        report = await analysis_service.generate_scouting_report(db, fighter_id)
        return report
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"{type(e).__name__}: {e}")


@router.get("/scouting/{fighter_id}", response_model=s.ScoutingReportOut)
def get_scouting(
    fighter_id: int,
    db: Session = Depends(get_db),
    user: m.User = Depends(get_current_user),
):
    """Obtiene el último reporte de scouting guardado para un peleador."""
    _own_fighter(db, fighter_id, user)
    report = (
        db.query(m.ScoutingReport)
        .filter(m.ScoutingReport.fighter_id == fighter_id)
        .order_by(m.ScoutingReport.created_at.desc())
        .first()
    )
    if not report:
        raise HTTPException(404, "Scouting no generado aún")
    return report


# ========== PERFIL SINTETIZADO ==========

@router.post("/profile", response_model=s.FighterProfileOut)
async def synthesize_profile(
    req: s.ProfileSynthesisRequest,
    db: Session = Depends(get_db),
    user: m.User = Depends(get_current_user),
):
    """Genera perfil táctico consolidado a partir de todos los análisis del peleador."""
    _own_fighter(db, req.fighter_id, user)
    try:
        profile = await analysis_service.synthesize_fighter_profile(
            db, req.fighter_id, req.engine
        )
        return profile
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/profile/{fighter_id}", response_model=s.FighterProfileOut)
def get_profile(
    fighter_id: int,
    db: Session = Depends(get_db),
    user: m.User = Depends(get_current_user),
):
    _own_fighter(db, fighter_id, user)
    profile = (
        db.query(m.FighterProfile)
        .filter(m.FighterProfile.fighter_id == fighter_id)
        .first()
    )
    if not profile:
        raise HTTPException(404, "Perfil no generado aún")
    return profile


# ========== PREDICCIÓN DE PELEA ==========

@router.post("/prediction", response_model=s.FightPredictionOut)
async def predict_fight(
    req: s.FightPredictionRequest,
    db: Session = Depends(get_db),
    user: m.User = Depends(get_current_user),
):
    """Predice ganador probable, método y ronda estimada entre dos peleadores."""
    _own_fighter(db, req.our_fighter_id, user)
    _own_fighter(db, req.opponent_id, user)
    try:
        return await analysis_service.predict_fight(
            db, req.our_fighter_id, req.opponent_id, req.engine
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"{type(e).__name__}: {e}")


# ========== PLAN DE COMBATE ==========

@router.post("/plan", response_model=s.FightPlanOut)
async def create_fight_plan(
    req: s.FightPlanRequest,
    db: Session = Depends(get_db),
    user: m.User = Depends(get_current_user),
):
    """
    FASE 2: Claude toma los reportes de scouting de ambos peleadores
    y construye el plan estratégico completo.

    Requiere que ambos peleadores tengan scouting generado y confirmado.
    """
    _own_fighter(db, req.our_fighter_id, user)
    _own_fighter(db, req.opponent_id, user)
    try:
        # Verificar que ambos peleadores tienen scouting
        our_scouting = (
            db.query(m.ScoutingReport)
            .filter(m.ScoutingReport.fighter_id == req.our_fighter_id)
            .order_by(m.ScoutingReport.created_at.desc())
            .first()
        )
        opp_scouting = (
            db.query(m.ScoutingReport)
            .filter(m.ScoutingReport.fighter_id == req.opponent_id)
            .order_by(m.ScoutingReport.created_at.desc())
            .first()
        )

        if not our_scouting:
            raise ValueError(
                "Nuestro peleador no tiene scouting generado. "
                "Ve al perfil del peleador y genera el scouting primero."
            )
        if not opp_scouting:
            raise ValueError(
                "El oponente no tiene scouting generado. "
                "Ve al perfil del oponente y genera el scouting primero."
            )

        plan = await analysis_service.generate_fight_plan_from_scouting(
            db,
            our_fighter_id=req.our_fighter_id,
            opponent_id=req.opponent_id,
            our_scouting=our_scouting,
            opp_scouting=opp_scouting,
            additional_context=req.additional_context,
        )

        # Generar PDF automáticamente
        our = fighter_service.get_fighter(db, plan.our_fighter_id)
        opp = fighter_service.get_fighter(db, plan.opponent_id)
        pdf_path = generate_pdf_for_plan(
            plan,
            our_bio=fighter_service.fighter_to_bio_dict(our),
            opponent_bio=fighter_service.fighter_to_bio_dict(opp),
        )
        plan.pdf_path = str(pdf_path)
        db.commit()
        db.refresh(plan)
        return plan
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/plan/{plan_id}", response_model=s.FightPlanOut)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    user: m.User = Depends(get_current_user),
):
    return _own_plan(db, plan_id, user)


@router.get("/plan/{plan_id}/pdf")
def download_plan_pdf(
    plan_id: int,
    db: Session = Depends(get_db),
    user: m.User = Depends(get_current_user),
):
    """Descarga el PDF del plan."""
    plan = _own_plan(db, plan_id, user)
    if not plan.pdf_path or not Path(plan.pdf_path).exists():
        from app.services import fighter_service as fs
        our = fs.get_fighter(db, plan.our_fighter_id)
        opp = fs.get_fighter(db, plan.opponent_id)
        pdf_path = generate_pdf_for_plan(
            plan,
            our_bio=fs.fighter_to_bio_dict(our),
            opponent_bio=fs.fighter_to_bio_dict(opp),
        )
        plan.pdf_path = str(pdf_path)
        db.commit()

    return FileResponse(
        plan.pdf_path,
        media_type="application/pdf",
        filename=f"plan_combate_{plan_id}.pdf",
    )
