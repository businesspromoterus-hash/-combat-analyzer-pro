"""
Modelos SQLAlchemy: peleadores, peleas, análisis y planes de combate.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class FighterRole(str, enum.Enum):
    """Nuestro peleador vs oponente."""
    OUR = "our"
    OPPONENT = "opponent"


class CombatSport(str, enum.Enum):
    BOXING = "boxing"
    MMA = "mma"
    JUDO = "judo"
    KICKBOXING = "kickboxing"
    MUAY_THAI = "muay_thai"
    BJJ = "bjj"
    KARATE = "karate"
    TAEKWONDO = "taekwondo"
    WRESTLING = "wrestling"
    OTHER = "other"


class Stance(str, enum.Enum):
    ORTHODOX = "orthodox"     # diestro
    SOUTHPAW = "southpaw"      # zurdo
    SWITCH = "switch"
    NA = "na"                  # judo / lucha


class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ========== FIGHTER ==========

class Fighter(Base):
    __tablename__ = "fighters"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(SAEnum(FighterRole), nullable=False, index=True)

    # Identidad
    name = Column(String(200), nullable=False)
    sport = Column(SAEnum(CombatSport), nullable=False)
    country = Column(String(100), nullable=True)

    # Datos físicos
    age = Column(Integer, nullable=True)
    weight_kg = Column(Float, nullable=True)
    division = Column(String(100), nullable=True)
    height_cm = Column(Float, nullable=True)
    reach_cm = Column(Float, nullable=True)
    stance = Column(SAEnum(Stance), default=Stance.ORTHODOX)

    # Récord y experiencia
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    ko_wins = Column(Integer, default=0)        # boxeo/MMA
    sub_wins = Column(Integer, default=0)        # MMA/BJJ
    ippon_wins = Column(Integer, default=0)      # judo
    years_experience = Column(Integer, nullable=True)

    # Notas libres del entrenador
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    fights = relationship("Fight", back_populates="fighter", cascade="all, delete-orphan")

    @property
    def record_str(self) -> str:
        return f"{self.wins}-{self.losses}-{self.draws}"


# ========== FIGHT (cada video/link de pelea analizado) ==========

class Fight(Base):
    __tablename__ = "fights"

    id = Column(Integer, primary_key=True, index=True)
    fighter_id = Column(Integer, ForeignKey("fighters.id", ondelete="CASCADE"), nullable=False)

    # Origen del video
    youtube_url = Column(String(500), nullable=True)
    local_file_path = Column(String(500), nullable=True)
    title = Column(String(300), nullable=True)
    opponent_name = Column(String(200), nullable=True)
    result = Column(String(50), nullable=True)   # "win-ko-r2", "loss-decision", etc.
    fight_date = Column(String(20), nullable=True)

    # Metadata extraída
    duration_seconds = Column(Integer, nullable=True)
    transcript = Column(Text, nullable=True)
    raw_metadata = Column(JSON, nullable=True)

    # Notas manuales del entrenador
    coach_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    fighter = relationship("Fighter", back_populates="fights")
    analyses = relationship("FightAnalysis", back_populates="fight", cascade="all, delete-orphan")


# ========== ANALYSIS (resultado del motor de IA) ==========

class FightAnalysis(Base):
    """Análisis de una pelea individual por un motor de IA."""
    __tablename__ = "fight_analyses"

    id = Column(Integer, primary_key=True, index=True)
    fight_id = Column(Integer, ForeignKey("fights.id", ondelete="CASCADE"), nullable=False)

    engine_used = Column(String(50), nullable=False)   # "gemini", "claude", "openai"
    status = Column(SAEnum(AnalysisStatus), default=AnalysisStatus.PENDING)

    # Resultado estructurado (JSON con todos los campos del análisis)
    # strengths, weaknesses, patterns, favorite_techniques, defensive_errors,
    # cardio, pressure_response, late_rounds, key_moments, etc.
    result = Column(JSON, nullable=True)

    error_message = Column(Text, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    fight = relationship("Fight", back_populates="analyses")


# ========== FIGHTER PROFILE (agregado de todos sus análisis) ==========

class FighterProfile(Base):
    """Perfil táctico consolidado de un peleador (síntesis de múltiples peleas)."""
    __tablename__ = "fighter_profiles"

    id = Column(Integer, primary_key=True, index=True)
    fighter_id = Column(Integer, ForeignKey("fighters.id", ondelete="CASCADE"), unique=True)

    # Síntesis estructurada
    profile = Column(JSON, nullable=False)   # estilo, fortalezas, debilidades, patrones, etc.
    engine_used = Column(String(50), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ========== FIGHT PLAN (plan completo de combate) ==========

class FightPlan(Base):
    """Plan estratégico completo: nuestro plan + plan del rival + contramedidas + sparrings + campamento."""
    __tablename__ = "fight_plans"

    id = Column(Integer, primary_key=True, index=True)
    our_fighter_id = Column(Integer, ForeignKey("fighters.id", ondelete="CASCADE"), nullable=False)
    opponent_id = Column(Integer, ForeignKey("fighters.id", ondelete="CASCADE"), nullable=False)

    # Plan estructurado (JSON con todas las secciones)
    plan = Column(JSON, nullable=False)
    engine_used = Column(String(50), nullable=False)

    # PDF generado
    pdf_path = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
