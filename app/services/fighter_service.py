"""Servicio de peleadores: CRUD + lógica de negocio."""
from sqlalchemy.orm import Session
from typing import Optional

from app.models import db_models as m
from app.models import schemas as s


def create_fighter(db: Session, data: s.FighterCreate) -> m.Fighter:
    fighter = m.Fighter(**data.model_dump())
    db.add(fighter)
    db.commit()
    db.refresh(fighter)
    return fighter


def get_fighter(db: Session, fighter_id: int) -> Optional[m.Fighter]:
    return db.query(m.Fighter).filter(m.Fighter.id == fighter_id).first()


def list_fighters(db: Session, role: Optional[m.FighterRole] = None) -> list[m.Fighter]:
    q = db.query(m.Fighter)
    if role:
        q = q.filter(m.Fighter.role == role)
    return q.order_by(m.Fighter.created_at.desc()).all()


def update_fighter(db: Session, fighter_id: int, data: s.FighterUpdate) -> Optional[m.Fighter]:
    fighter = get_fighter(db, fighter_id)
    if not fighter:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(fighter, k, v)
    db.commit()
    db.refresh(fighter)
    return fighter


def delete_fighter(db: Session, fighter_id: int) -> bool:
    fighter = get_fighter(db, fighter_id)
    if not fighter:
        return False
    db.delete(fighter)
    db.commit()
    return True


def fighter_to_bio_dict(fighter: m.Fighter) -> dict:
    """Convierte un Fighter a dict bio para alimentar al motor de IA."""
    return {
        "name": fighter.name,
        "sport": fighter.sport.value if fighter.sport else None,
        "country": fighter.country,
        "age": fighter.age,
        "weight_kg": fighter.weight_kg,
        "division": fighter.division,
        "height_cm": fighter.height_cm,
        "reach_cm": fighter.reach_cm,
        "stance": fighter.stance.value if fighter.stance else None,
        "record": fighter.record_str,
        "ko_wins": fighter.ko_wins,
        "sub_wins": fighter.sub_wins,
        "ippon_wins": fighter.ippon_wins,
        "years_experience": fighter.years_experience,
        "notes": fighter.notes,
    }
