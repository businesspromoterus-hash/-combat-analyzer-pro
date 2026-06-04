"""
API de autenticación: registro, login, logout.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_session_token
from app.models import db_models as m
from app.utils.email_sender import send_welcome_email

router = APIRouter(prefix="/auth", tags=["auth"])

SESSION_DURATION_DAYS = 30
COOKIE_NAME = "combat_session"


# ── Schemas ───────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


# ── Helper: obtener usuario desde cookie ─────────────────────────────────────

def get_current_user(request: Request, db: Session = Depends(get_db)) -> m.User:
    """Obtiene el usuario autenticado desde la cookie de sesión."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")

    session = (
        db.query(m.UserSession)
        .filter(m.UserSession.token == token)
        .first()
    )
    if not session or not session.is_valid:
        raise HTTPException(status_code=401, detail="Sesión expirada")

    return session.user


def get_current_user_optional(request: Request, db: Session = Depends(get_db)):
    """Igual pero retorna None si no hay sesión (para páginas públicas)."""
    try:
        return get_current_user(request, db)
    except HTTPException:
        return None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register")
def register(
    req: RegisterRequest,
    response: Response,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Registra un nuevo entrenador."""
    # Normalizar el email una sola vez (minúsculas + sin espacios) y usar ese
    # mismo valor para verificar duplicados y para guardar. Antes la verificación
    # usaba .lower() sin .strip() mientras que el guardado sí hacía .strip(), lo
    # que permitía colar correos duplicados con espacios alrededor.
    email = req.email.lower().strip()

    existing = db.query(m.User).filter(m.User.email == email).first()
    if existing:
        raise HTTPException(400, "Ya existe una cuenta con ese email")

    user = m.User(
        email=email,
        name=req.name.strip(),
        hashed_password=hash_password(req.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Respaldo ante condiciones de carrera: la columna email es UNIQUE, así
        # que si dos registros simultáneos usan el mismo correo, garantizamos que
        # solo uno se cree y el otro reciba un error claro.
        db.rollback()
        raise HTTPException(400, "Ya existe una cuenta con ese email")
    db.refresh(user)

    # Crear sesión automáticamente
    token = create_session_token()
    session = m.UserSession(
        user_id=user.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(days=SESSION_DURATION_DAYS),
    )
    db.add(session)
    db.commit()

    response.set_cookie(
        COOKIE_NAME, token,
        max_age=SESSION_DURATION_DAYS * 86400,
        httponly=True,
        samesite="lax",
    )

    # Correo de bienvenida — best-effort, en segundo plano para no bloquear la
    # respuesta ni romper el registro si el envío falla.
    background_tasks.add_task(send_welcome_email, user.email, user.name)

    return {"ok": True, "user": {"id": user.id, "name": user.name, "email": user.email}}


@router.post("/login")
def login(req: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """Login de entrenador."""
    user = db.query(m.User).filter(m.User.email == req.email.lower()).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(401, "Email o contraseña incorrectos")

    token = create_session_token()
    session = m.UserSession(
        user_id=user.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(days=SESSION_DURATION_DAYS),
    )
    db.add(session)
    db.commit()

    response.set_cookie(
        COOKIE_NAME, token,
        max_age=SESSION_DURATION_DAYS * 86400,
        httponly=True,
        samesite="lax",
    )
    return {"ok": True, "user": {"id": user.id, "name": user.name, "email": user.email}}


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    """Cierra sesión."""
    token = request.cookies.get(COOKIE_NAME)
    if token:
        db.query(m.UserSession).filter(m.UserSession.token == token).delete()
        db.commit()
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@router.get("/me")
def me(user: m.User = Depends(get_current_user)):
    """Retorna el usuario autenticado actual."""
    return {"id": user.id, "name": user.name, "email": user.email}
