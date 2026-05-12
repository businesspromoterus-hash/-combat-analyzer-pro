"""Endpoints de análisis IA: pelea, perfil sintetizado y plan completo."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from app.core.database import get_db
from app.models import db_models as m
from app.models import schemas as s
from app.services import analysis_service, fighter_service
from app.utils.pdf_generator import generate_pdf_for_plan
from app.engines import list_available_engines


router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/engines")
def get_engines():
    """Lista motores disponibles y cuáles están configurados."""
    return {"engines": list_available_engines()}


# ========== ANÁLISIS DE PELEA INDIVIDUAL ==========

@router.post("/fight", response_model=s.AnalysisOut)
async def analyze_fight(req: s.AnalysisRequest, db: Session = Depends(get_db)):
    """
    Analiza una pelea con el motor especificado (o el default).
    Operación síncrona: devuelve cuando termina (puede tardar minutos).
    """
    try:
        analysis = await analysis_service.analyze_fight(db, req.fight_id, req.engine)
        return analysis
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"{type(e).__name__}: {e}")


@router.get("/fight/{fight_id}", response_model=list[s.AnalysisOut])
def get_fight_analyses(fight_id: int, db: Session = Depends(get_db)):
    return (
        db.query(m.FightAnalysis)
        .filter(m.FightAnalysis.fight_id == fight_id)
        .order_by(m.FightAnalysis.created_at.desc())
        .all()
    )


# ========== SÍNTESIS DE PERFIL ==========

@router.post("/profile", response_model=s.FighterProfileOut)
async def synthesize_profile(req: s.ProfileSynthesisRequest, db: Session = Depends(get_db)):
    """Genera perfil táctico consolidado a partir de todos los análisis del peleador."""
    try:
        profile = await analysis_service.synthesize_fighter_profile(
            db, req.fighter_id, req.engine
        )
        return profile
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/profile/{fighter_id}", response_model=s.FighterProfileOut)
def get_profile(fighter_id: int, db: Session = Depends(get_db)):
    profile = (
        db.query(m.FighterProfile)
        .filter(m.FighterProfile.fighter_id == fighter_id)
        .first()
    )
    if not profile:
        raise HTTPException(404, "Perfil no generado aún")
    return profile


# ========== PLAN DE COMBATE ==========

@router.post("/plan", response_model=s.FightPlanOut)
async def create_fight_plan(req: s.FightPlanRequest, db: Session = Depends(get_db)):
    """Genera el plan de combate completo cruzando ambos peleadores."""
    try:
        plan = await analysis_service.generate_fight_plan(
            db,
            our_fighter_id=req.our_fighter_id,
            opponent_id=req.opponent_id,
            engine_name=req.engine,
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
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(m.FightPlan).filter(m.FightPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(404, "Plan no encontrado")
    return plan


@router.get("/plan/{plan_id}/pdf")
def download_plan_pdf(plan_id: int, db: Session = Depends(get_db)):
    """Descarga el PDF del plan."""
    plan = db.query(m.FightPlan).filter(m.FightPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(404, "Plan no encontrado")
    if not plan.pdf_path or not Path(plan.pdf_path).exists():
        # Generar PDF si no existe
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
