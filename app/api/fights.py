"""Endpoints de peleas: registro de videos y links."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models import db_models as m
from app.models import schemas as s
from app.services import fight_service, fighter_service


router = APIRouter(prefix="/api/fights", tags=["fights"])


def _require_owned_fighter(db: Session, fighter_id: int, user: m.User) -> m.Fighter:
    fighter = fighter_service.get_fighter(db, fighter_id, owner_id=user.id)
    if not fighter:
        raise HTTPException(404, "Peleador no encontrado")
    return fighter


@router.post("/url", response_model=s.FightOut, status_code=201)
def add_youtube(
    data: s.FightCreate,
    db: Session = Depends(get_db),
    user: m.User = Depends(get_current_user),
):
    if not data.youtube_url or not fight_service.is_youtube_url(data.youtube_url):
        raise HTTPException(400, "URL de YouTube inválida")
    _require_owned_fighter(db, data.fighter_id, user)
    return fight_service.create_fight_from_url(db, data)


@router.post("/upload", response_model=s.FightOut, status_code=201)
async def upload_video(
    fighter_id: int = Form(...),
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    opponent_name: Optional[str] = Form(None),
    result: Optional[str] = Form(None),
    coach_notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: m.User = Depends(get_current_user),
):
    _require_owned_fighter(db, fighter_id, user)
    try:
        return await fight_service.create_fight_from_upload(
            db, fighter_id, file, title, opponent_name, result, coach_notes
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/fighter/{fighter_id}", response_model=list[s.FightOut])
def list_for_fighter(
    fighter_id: int,
    db: Session = Depends(get_db),
    user: m.User = Depends(get_current_user),
):
    _require_owned_fighter(db, fighter_id, user)
    return fight_service.list_fights_for_fighter(db, fighter_id)


@router.get("/{fight_id}", response_model=s.FightOut)
def get_one(
    fight_id: int,
    db: Session = Depends(get_db),
    user: m.User = Depends(get_current_user),
):
    fight = fight_service.get_owned_fight(db, fight_id, owner_id=user.id)
    if not fight:
        raise HTTPException(404, "Pelea no encontrada")
    return fight


@router.delete("/{fight_id}", status_code=204)
def delete(
    fight_id: int,
    db: Session = Depends(get_db),
    user: m.User = Depends(get_current_user),
):
    if not fight_service.get_owned_fight(db, fight_id, owner_id=user.id):
        raise HTTPException(404, "Pelea no encontrada")
    fight_service.delete_fight(db, fight_id)
