"""
Modelos SQLAlchemy — con autenticación multi-usuario.
Cada entrenador tiene su cuenta y solo ve sus propios datos.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime,
    ForeignKey, JSON, Enum as SAEnum, Boolean
)
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


# ========== USUARIO / ENTRENADOR ==========

class User(Base):
    """Cuenta de entrenador. Cada usuario tiene sus propios peleadores y planes."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    hashed_password = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    fighters = relationship("Fighter", back_populates="owner", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")


class UserSession(Base):
    """Sesiones activas de usuario."""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(200), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="sessions")

    @property
    def is_valid(self) -> bool:
        return datetime.utcnow() < self.expires_at


# ========== ENUMS ==========

class FighterRole(str, enum.Enum):
    OUR = "our"
    OPPONENT = "opponent"


class CombatSport(str, enum.Enum):
    BOXING = "boxing"           # Boxeo
    MMA = "mma"                 # MMA
    BKFC = "bkfc"               # BKFC — Bare Knuckle
    KICKBOXING = "kickboxing"   # Kickboxing
    MUAY_THAI = "muay_thai"     # Muay Thai
    BJJ = "bjj"                 # BJJ — Brazilian Jiu-Jitsu
    JUDO = "judo"               # Judo
    KARATE = "karate"           # Karate
    KARATE_COMBAT = "karate_combat"  # Karate Combat
    TAEKWONDO = "taekwondo"     # Taekwondo
    WRESTLING = "wrestling"     # Lucha
    OTHER = "other"             # Otro


class Stance(str, enum.Enum):
    ORTHODOX = "orthodox"
    SOUTHPAW = "southpaw"
    SWITCH = "switch"
    NA = "na"


class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ========== FIGHTER ==========

class Fighter(Base):
    __tablename__ = "fighters"

    id = Column(Integer, primary_key=True, index=True)

    # Dueño del peleador — cada entrenador ve solo los suyos
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)  # nullable hasta cablear ownership en los routers

    role = Column(SAEnum(FighterRole), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    sport = Column(SAEnum(CombatSport), nullable=False)
    country = Column(String(100), nullable=True)
    age = Column(Integer, nullable=True)
    weight_kg = Column(Float, nullable=True)
    division = Column(String(100), nullable=True)
    height_cm = Column(Float, nullable=True)
    reach_cm = Column(Float, nullable=True)
    stance = Column(SAEnum(Stance), default=Stance.ORTHODOX)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    ko_wins = Column(Integer, default=0)
    sub_wins = Column(Integer, default=0)
    ippon_wins = Column(Integer, default=0)
    years_experience = Column(Integer, nullable=True)  # legado — total (se mantiene por compatibilidad)
    years_experience_pro = Column(Integer, nullable=True)       # experiencia profesional
    years_experience_amateur = Column(Integer, nullable=True)   # experiencia amateur
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="fighters")
    fights = relationship("Fight", back_populates="fighter", cascade="all, delete-orphan")

    @property
    def record_str(self) -> str:
        return f"{self.wins}-{self.losses}-{self.draws}"


# ========== FIGHT ==========

class Fight(Base):
    __tablename__ = "fights"

    id = Column(Integer, primary_key=True, index=True)
    fighter_id = Column(Integer, ForeignKey("fighters.id", ondelete="CASCADE"), nullable=False)
    youtube_url = Column(String(500), nullable=True)
    local_file_path = Column(String(500), nullable=True)
    title = Column(String(300), nullable=True)
    opponent_name = Column(String(200), nullable=True)
    result = Column(String(50), nullable=True)
    fight_date = Column(String(20), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    transcript = Column(Text, nullable=True)
    raw_metadata = Column(JSON, nullable=True)
    coach_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    fighter = relationship("Fighter", back_populates="fights")
    analyses = relationship("FightAnalysis", back_populates="fight", cascade="all, delete-orphan")


# ========== FIGHT ANALYSIS ==========

class FightAnalysis(Base):
    __tablename__ = "fight_analyses"

    id = Column(Integer, primary_key=True, index=True)
    fight_id = Column(Integer, ForeignKey("fights.id", ondelete="CASCADE"), nullable=False)
    engine_used = Column(String(50), nullable=False)
    status = Column(SAEnum(AnalysisStatus), default=AnalysisStatus.PENDING)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    fight = relationship("Fight", back_populates="analyses")


# ========== FIGHTER PROFILE ==========

class FighterProfile(Base):
    __tablename__ = "fighter_profiles"

    id = Column(Integer, primary_key=True, index=True)
    fighter_id = Column(Integer, ForeignKey("fighters.id", ondelete="CASCADE"), unique=True)
    profile = Column(JSON, nullable=False)
    engine_used = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ========== SCOUTING REPORT ==========

class ScoutingReport(Base):
    __tablename__ = "scouting_reports"

    id = Column(Integer, primary_key=True, index=True)
    fighter_id = Column(Integer, ForeignKey("fighters.id", ondelete="CASCADE"), nullable=False, index=True)
    report = Column(JSON, nullable=False)
    fights_analyzed = Column(Integer, default=0)
    engine_used = Column(String(50), nullable=False, default="gemini")
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)


# ========== FIGHT PLAN ==========

class FightPlan(Base):
    __tablename__ = "fight_plans"

    id = Column(Integer, primary_key=True, index=True)
    our_fighter_id = Column(Integer, ForeignKey("fighters.id", ondelete="CASCADE"), nullable=False)
    opponent_id = Column(Integer, ForeignKey("fighters.id", ondelete="CASCADE"), nullable=False)
    plan = Column(JSON, nullable=False)
    engine_used = Column(String(50), nullable=False)
    pdf_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
