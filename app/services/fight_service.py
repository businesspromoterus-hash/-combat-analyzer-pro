"""Servicio de peleas: registro de videos/links y manejo de archivos."""
import re
import uuid
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.core.config import settings
from app.models import db_models as m
from app.models import schemas as s


YOUTUBE_RE = re.compile(
    r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([A-Za-z0-9_-]{11})"
)


def is_youtube_url(url: str) -> bool:
    return bool(YOUTUBE_RE.search(url or ""))


def extract_youtube_id(url: str) -> Optional[str]:
    m_ = YOUTUBE_RE.search(url or "")
    return m_.group(1) if m_ else None


def create_fight_from_url(db: Session, data: s.FightCreate) -> m.Fight:
    fight = m.Fight(
        fighter_id=data.fighter_id,
        youtube_url=data.youtube_url,
        title=data.title,
        opponent_name=data.opponent_name,
        result=data.result,
        fight_date=data.fight_date,
        coach_notes=data.coach_notes,
    )
    db.add(fight)
    db.commit()
    db.refresh(fight)
    return fight


async def create_fight_from_upload(
    db: Session,
    fighter_id: int,
    file: UploadFile,
    title: Optional[str] = None,
    opponent_name: Optional[str] = None,
    result: Optional[str] = None,
    coach_notes: Optional[str] = None,
) -> m.Fight:
    """Guarda archivo de video subido y crea registro."""
    ext = Path(file.filename).suffix.lower() or ".mp4"
    if ext not in {".mp4", ".mov", ".avi", ".mkv", ".webm"}:
        raise ValueError(f"Formato no soportado: {ext}")

    file_name = f"{uuid.uuid4().hex}{ext}"
    file_path = settings.upload_path / file_name

    # Stream a disco (no cargar todo a memoria)
    size = 0
    max_size = settings.max_video_size_mb * 1024 * 1024
    with open(file_path, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > max_size:
                out.close()
                file_path.unlink(missing_ok=True)
                raise ValueError(f"Video supera el máximo de {settings.max_video_size_mb}MB")
            out.write(chunk)

    fight = m.Fight(
        fighter_id=fighter_id,
        local_file_path=str(file_path),
        title=title or file.filename,
        opponent_name=opponent_name,
        result=result,
        coach_notes=coach_notes,
    )
    db.add(fight)
    db.commit()
    db.refresh(fight)
    return fight


def get_fight(db: Session, fight_id: int) -> Optional[m.Fight]:
    return db.query(m.Fight).filter(m.Fight.id == fight_id).first()


def get_owned_fight(
    db: Session, fight_id: int, owner_id: Optional[int] = None
) -> Optional[m.Fight]:
    """Devuelve la pelea solo si pertenece a un peleador del owner indicado."""
    fight = get_fight(db, fight_id)
    if not fight:
        return None
    if owner_id is not None and (fight.fighter is None or fight.fighter.owner_id != owner_id):
        return None
    return fight


def list_fights_for_fighter(db: Session, fighter_id: int) -> list[m.Fight]:
    return (
        db.query(m.Fight)
        .filter(m.Fight.fighter_id == fighter_id)
        .order_by(m.Fight.created_at.desc())
        .all()
    )


def delete_fight(db: Session, fight_id: int) -> bool:
    fight = get_fight(db, fight_id)
    if not fight:
        return False
    # borrar archivo local si existe
    if fight.local_file_path:
        Path(fight.local_file_path).unlink(missing_ok=True)
    db.delete(fight)
    db.commit()
    return True
