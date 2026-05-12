"""Endpoints de peleadores."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import db_models as m
from app.models import schemas as s
from app.services import fighter_service


router = APIRouter(prefix="/api/fighters", tags=["fighters"])


@router.post("", response_model=s.FighterOut, status_code=201)
def create(data: s.FighterCreate, db: Session = Depends(get_db)):
    fighter = fighter_service.create_fighter(db, data)
    return fighter


@router.get("", response_model=list[s.FighterOut])
def list_all(
    role: Optional[m.FighterRole] = Query(None),
    db: Session = Depends(get_db),
):
    return fighter_service.list_fighters(db, role=role)


@router.get("/{fighter_id}", response_model=s.FighterOut)
def get_one(fighter_id: int, db: Session = Depends(get_db)):
    fighter = fighter_service.get_fighter(db, fighter_id)
    if not fighter:
        raise HTTPException(404, "Peleador no encontrado")
    return fighter


@router.patch("/{fighter_id}", response_model=s.FighterOut)
def update(fighter_id: int, data: s.FighterUpdate, db: Session = Depends(get_db)):
    fighter = fighter_service.update_fighter(db, fighter_id, data)
    if not fighter:
        raise HTTPException(404, "Peleador no encontrado")
    return fighter


@router.delete("/{fighter_id}", status_code=204)
def delete(fighter_id: int, db: Session = Depends(get_db)):
    if not fighter_service.delete_fighter(db, fighter_id):
        raise HTTPException(404, "Peleador no encontrado")
