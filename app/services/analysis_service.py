"""
Servicio de análisis: orquesta los motores de IA.

ARQUITECTURA DE 2 FASES:
- FASE 1: Gemini analiza todas las peleas → genera reporte de scouting completo
- FASE 2: Claude recibe ambos reportes de scouting → construye plan estratégico

El entrenador revisa y confirma el scouting ANTES de que Claude genere el plan.
"""
import time
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models import db_models as m
from app.services import fighter_service
from app.services import fight_service
from app.engines import (
    get_video_engine, get_strategy_engine,
    FightAnalysisResult, FighterStyleProfile, CompleteFightPlan,
)


# ========== ANÁLISIS DE UNA PELEA INDIVIDUAL ==========

async def analyze_fight(
    db: Session,
    fight_id: int,
    engine_name: Optional[str] = None,
) -> m.FightAnalysis:
    """Analiza una pelea individual con Gemini y guarda el resultado."""
    fight = fight_service.get_fight(db, fight_id)
    if not fight:
        raise ValueError(f"Pelea {fight_id} no encontrada")

    fighter = fighter_service.get_fighter(db, fight.fighter_id)
    if not fighter:
        raise ValueError("Peleador de la pelea no encontrado")

    engine = get_video_engine(engine_name)

    analysis = m.FightAnalysis(
        fight_id=fight_id,
        engine_used=engine.name,
        status=m.AnalysisStatus.PROCESSING,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    t0 = time.time()
    try:
        video_source = fight.local_file_path or fight.youtube_url
        if not video_source:
            raise ValueError("La pelea no tiene video ni URL asociados")

        result = await engine.analyze_fight_video(
            video_source=video_source,
            fighter_name=fighter.name,
            sport=fighter.sport.value,
            coach_notes=fight.coach_notes,
        )

        analysis.result = result.model_dump()
        analysis.status = m.AnalysisStatus.COMPLETED
        analysis.completed_at = datetime.utcnow()
        analysis.duration_seconds = time.time() - t0

    except Exception as e:
        analysis.status = m.AnalysisStatus.FAILED
        analysis.error_message = f"{type(e).__name__}: {e}"
        analysis.duration_seconds = time.time() - t0

    db.commit()
    db.refresh(analysis)
    return analysis


# ========== FASE 1: SCOUTING COMPLETO (GEMINI) ==========

async def generate_scouting_report(
    db: Session,
    fighter_id: int,
) -> m.ScoutingReport:
    """
    FASE 1: Gemini analiza TODAS las peleas del peleador y genera
    un reporte de scouting profesional completo.

    El entrenador debe revisar este reporte ANTES de generar el plan.
    """
    fighter = fighter_service.get_fighter(db, fighter_id)
    if not fighter:
        raise ValueError(f"Peleador {fighter_id} no encontrado")

    fights = fight_service.list_fights_for_fighter(db, fighter_id)

    # Recoger todos los análisis COMPLETED
    individual_analyses: list[FightAnalysisResult] = []
    for fight in fights:
        for a in fight.analyses:
            if a.status == m.AnalysisStatus.COMPLETED and a.result:
                try:
                    individual_analyses.append(FightAnalysisResult(**a.result))
                except Exception:
                    continue

    if not individual_analyses:
        raise ValueError(
            f"{fighter.name} no tiene peleas analizadas aún. "
            f"Agrega peleas (YouTube o video), analízalas y luego genera el scouting."
        )

    # Gemini sintetiza todos los análisis en un reporte de scouting
    engine = get_video_engine("gemini")
    bio = fighter_service.fighter_to_bio_dict(fighter)

    scouting_data = await engine.synthesize_fighter_profile(
        fighter_name=fighter.name,
        sport=fighter.sport.value,
        individual_analyses=individual_analyses,
        bio_data=bio,
    )

    # Guardar en DB
    report = m.ScoutingReport(
        fighter_id=fighter_id,
        report=scouting_data.model_dump(),
        fights_analyzed=len(individual_analyses),
        engine_used=engine.name,
        status="pending",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


# ========== SÍNTESIS DE PERFIL (compatible con flujo anterior) ==========

async def synthesize_fighter_profile(
    db: Session,
    fighter_id: int,
    engine_name: Optional[str] = None,
) -> m.FighterProfile:
    """Sintetiza perfil táctico consolidado (mantiene compatibilidad)."""
    fighter = fighter_service.get_fighter(db, fighter_id)
    if not fighter:
        raise ValueError(f"Peleador {fighter_id} no encontrado")

    fights = fight_service.list_fights_for_fighter(db, fighter_id)

    individual_analyses: list[FightAnalysisResult] = []
    for fight in fights:
        for a in fight.analyses:
            if a.status == m.AnalysisStatus.COMPLETED and a.result:
                try:
                    individual_analyses.append(FightAnalysisResult(**a.result))
                except Exception:
                    continue

    if not individual_analyses:
        bio = fighter_service.fighter_to_bio_dict(fighter)
        profile_data = FighterStyleProfile(
            fighter_name=fighter.name,
            overall_style="Sin análisis de video disponibles aún",
            consistent_strengths=[],
            consistent_weaknesses=[],
            signature_techniques=[],
            recurring_defensive_holes=[],
            cardio_profile="N/A — sube peleas para análisis",
            mental_profile="N/A",
            historical_losses_pattern="N/A",
            matchup_history_vs_similar="N/A",
            summary=f"Perfil pendiente: aún no hay peleas analizadas para {fighter.name}.",
        )
        engine_used = "none"
    else:
        engine = get_strategy_engine(engine_name)
        bio = fighter_service.fighter_to_bio_dict(fighter)
        profile_data = await engine.synthesize_fighter_profile(
            fighter_name=fighter.name,
            sport=fighter.sport.value,
            individual_analyses=individual_analyses,
            bio_data=bio,
        )
        engine_used = engine.name

    existing = (
        db.query(m.FighterProfile)
        .filter(m.FighterProfile.fighter_id == fighter_id)
        .first()
    )
    if existing:
        existing.profile = profile_data.model_dump()
        existing.engine_used = engine_used
        db.commit()
        db.refresh(existing)
        return existing

    profile = m.FighterProfile(
        fighter_id=fighter_id,
        profile=profile_data.model_dump(),
        engine_used=engine_used,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


# ========== PREDICCIÓN DE PELEA ==========

async def predict_fight(
    db: Session,
    our_fighter_id: int,
    opponent_id: int,
    engine_name: Optional[str] = None,
) -> dict:
    """
    Predice ganador probable, método y ronda estimada cruzando ambos peleadores.
    Usa el scouting existente como contexto si está disponible.
    """
    our_fighter = fighter_service.get_fighter(db, our_fighter_id)
    opponent = fighter_service.get_fighter(db, opponent_id)
    if not our_fighter or not opponent:
        raise ValueError("Uno de los peleadores no existe")

    def latest_scouting(fid: int):
        rep = (
            db.query(m.ScoutingReport)
            .filter(m.ScoutingReport.fighter_id == fid)
            .order_by(m.ScoutingReport.created_at.desc())
            .first()
        )
        return rep.report if rep else None

    engine = get_strategy_engine(engine_name or "claude")

    prediction = await engine.predict_fight(
        our_bio=fighter_service.fighter_to_bio_dict(our_fighter),
        opponent_bio=fighter_service.fighter_to_bio_dict(opponent),
        sport=our_fighter.sport.value,
        our_context=latest_scouting(our_fighter_id),
        opponent_context=latest_scouting(opponent_id),
    )

    prediction["our_fighter"] = our_fighter.name
    prediction["opponent"] = opponent.name
    return prediction


# ========== FASE 2: PLAN ESTRATÉGICO (CLAUDE) ==========

async def generate_fight_plan_from_scouting(
    db: Session,
    our_fighter_id: int,
    opponent_id: int,
    our_scouting: m.ScoutingReport,
    opp_scouting: m.ScoutingReport,
    additional_context: Optional[str] = None,
) -> m.FightPlan:
    """
    FASE 2: Claude recibe los reportes de scouting de ambos peleadores
    y construye el plan estratégico completo.
    """
    our_fighter = fighter_service.get_fighter(db, our_fighter_id)
    opponent = fighter_service.get_fighter(db, opponent_id)
    if not our_fighter or not opponent:
        raise ValueError("Uno de los peleadores no existe")

    engine = get_strategy_engine("claude")

    our_profile = FighterStyleProfile(**our_scouting.report)
    opp_profile = FighterStyleProfile(**opp_scouting.report)

    plan_data: CompleteFightPlan = await engine.generate_fight_plan(
        our_profile=our_profile,
        our_bio=fighter_service.fighter_to_bio_dict(our_fighter),
        opponent_profile=opp_profile,
        opponent_bio=fighter_service.fighter_to_bio_dict(opponent),
        sport=our_fighter.sport.value,
        additional_context=additional_context,
    )

    plan = m.FightPlan(
        our_fighter_id=our_fighter_id,
        opponent_id=opponent_id,
        plan=plan_data.model_dump(),
        engine_used=engine.name,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


# ========== PLAN COMPLETO (flujo anterior, mantiene compatibilidad) ==========

async def generate_fight_plan(
    db: Session,
    our_fighter_id: int,
    opponent_id: int,
    engine_name: Optional[str] = None,
    additional_context: Optional[str] = None,
) -> m.FightPlan:
    """Plan estratégico completo (flujo anterior — mantiene compatibilidad)."""
    our_fighter = fighter_service.get_fighter(db, our_fighter_id)
    opponent = fighter_service.get_fighter(db, opponent_id)
    if not our_fighter or not opponent:
        raise ValueError("Uno de los peleadores no existe")

    our_profile_record = (
        db.query(m.FighterProfile)
        .filter(m.FighterProfile.fighter_id == our_fighter_id)
        .first()
    )
    if not our_profile_record:
        our_profile_record = await synthesize_fighter_profile(db, our_fighter_id, engine_name)

    opp_profile_record = (
        db.query(m.FighterProfile)
        .filter(m.FighterProfile.fighter_id == opponent_id)
        .first()
    )
    if not opp_profile_record:
        opp_profile_record = await synthesize_fighter_profile(db, opponent_id, engine_name)

    engine = get_strategy_engine(engine_name)
    our_profile = FighterStyleProfile(**our_profile_record.profile)
    opp_profile = FighterStyleProfile(**opp_profile_record.profile)

    plan_data: CompleteFightPlan = await engine.generate_fight_plan(
        our_profile=our_profile,
        our_bio=fighter_service.fighter_to_bio_dict(our_fighter),
        opponent_profile=opp_profile,
        opponent_bio=fighter_service.fighter_to_bio_dict(opponent),
        sport=our_fighter.sport.value,
        additional_context=additional_context,
    )

    plan = m.FightPlan(
        our_fighter_id=our_fighter_id,
        opponent_id=opponent_id,
        plan=plan_data.model_dump(),
        engine_used=engine.name,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan
