"""Endpoints de peleadores."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models import db_models as m
from app.models import schemas as s
from app.services import fighter_service


router = APIRouter(prefix="/api/fighters", tags=["fighters"])


@router.post("", response_model=s.FighterOut, status_code=201)
def create(
    data: s.FighterCreate,
    db: Session = Depends(get_db),
    user: m.User = Depends(get_current_user),
):
    fighter = fighter_service.create_fighter(db, data, owner_id=user.id)
    return fighter


@router.get("", response_model=list[s.FighterOut])
def list_all(
    role: Optional[m.FighterRole] = Query(None),
    db: Session = Depends(get_db),
    user: m.User = Depends(get_current_user),
):
    return fighter_service.list_fighters(db, role=role, owner_id=user.id)


@router.get("/{fighter_id}", response_model=s.FighterOut)
def get_one(
    fighter_id: int,
    db: Session = Depends(get_db),
    user: m.User = Depends(get_current_user),
):
    fighter = fighter_service.get_fighter(db, fighter_id, owner_id=user.id)
    if not fighter:
        raise HTTPException(404, "Peleador no encontrado")
    return fighter


@router.patch("/{fighter_id}", response_model=s.FighterOut)
def update(
    fighter_id: int,
    data: s.FighterUpdate,
    db: Session = Depends(get_db),
    user: m.User = Depends(get_current_user),
):
    fighter = fighter_service.update_fighter(db, fighter_id, data, owner_id=user.id)
    if not fighter:
        raise HTTPException(404, "Peleador no encontrado")
    return fighter


@router.delete("/{fighter_id}", status_code=204)
def delete(
    fighter_id: int,
    db: Session = Depends(get_db),
    user: m.User = Depends(get_current_user),
):
    if not fighter_service.delete_fighter(db, fighter_id, owner_id=user.id):
        raise HTTPException(404, "Peleador no encontrado")
