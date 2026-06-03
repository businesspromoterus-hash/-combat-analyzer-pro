"""
Esquemas Pydantic para validación de API.
"""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field

from app.models.db_models import FighterRole, CombatSport, Stance, AnalysisStatus


# ========== FIGHTER ==========

class FighterBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    sport: CombatSport
    country: Optional[str] = None
    age: Optional[int] = Field(None, ge=10, le=80)
    weight_kg: Optional[float] = Field(None, ge=20, le=300)
    division: Optional[str] = None
    height_cm: Optional[float] = Field(None, ge=100, le=250)
    reach_cm: Optional[float] = Field(None, ge=100, le=260)
    stance: Stance = Stance.ORTHODOX
    wins: int = 0
    losses: int = 0
    draws: int = 0
    ko_wins: int = 0
    sub_wins: int = 0
    ippon_wins: int = 0
    years_experience: Optional[int] = None
    notes: Optional[str] = None


class FighterCreate(FighterBase):
    role: FighterRole


class FighterUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    reach_cm: Optional[float] = None
    stance: Optional[Stance] = None
    wins: Optional[int] = None
    losses: Optional[int] = None
    draws: Optional[int] = None
    notes: Optional[str] = None


class FighterOut(FighterBase):
    id: int
    role: FighterRole
    created_at: datetime
    record_str: str

    class Config:
        from_attributes = True


# ========== FIGHT ==========

class FightCreate(BaseModel):
    fighter_id: int
    youtube_url: Optional[str] = None
    title: Optional[str] = None
    opponent_name: Optional[str] = None
    result: Optional[str] = None
    fight_date: Optional[str] = None
    coach_notes: Optional[str] = None


class FightOut(BaseModel):
    id: int
    fighter_id: int
    youtube_url: Optional[str]
    local_file_path: Optional[str]
    title: Optional[str]
    opponent_name: Optional[str]
    result: Optional[str]
    fight_date: Optional[str]
    coach_notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ========== ANALYSIS ==========

class AnalysisRequest(BaseModel):
    fight_id: int
    engine: Optional[str] = None


class AnalysisOut(BaseModel):
    id: int
    fight_id: int
    engine_used: str
    status: AnalysisStatus
    result: Optional[dict] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ========== FIGHTER PROFILE ==========

class ProfileSynthesisRequest(BaseModel):
    fighter_id: int
    engine: Optional[str] = None


class FighterProfileOut(BaseModel):
    id: int
    fighter_id: int
    profile: dict
    engine_used: str
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== SCOUTING REPORT (NUEVO) ==========

class ScoutingReportOut(BaseModel):
    id: int
    fighter_id: int
    report: dict
    fights_analyzed: int
    engine_used: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ========== FIGHT PLAN ==========

class FightPlanRequest(BaseModel):
    our_fighter_id: int
    opponent_id: int
    engine: Optional[str] = None
    additional_context: Optional[str] = None


class FightPlanOut(BaseModel):
    id: int
    our_fighter_id: int
    opponent_id: int
    plan: dict
    engine_used: str
    pdf_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
