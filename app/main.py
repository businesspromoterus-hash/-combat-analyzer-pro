"""
Punto de entrada principal — con autenticación.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import pathlib

from app.core.database import engine, get_db
from app.core.migrations import run_migrations
from app.core.config import settings
from app.models import db_models as m
from app.api import fighters, fights, analysis, pages
from app.api.auth import router as auth_router, get_current_user_optional, COOKIE_NAME
from app.api.fighter_search import router as search_router
from app.api.chat import router as chat_router


# ── Crear tablas al arrancar ──────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    m.Base.metadata.create_all(bind=engine)
    run_migrations(engine)
    if settings.environment == "production" and not settings.session_secret:
        print("[WARN] SESSION_SECRET no está configurada en producción. "
              "Configúrala en Railway (Variables) para sesiones seguras.")
    pathlib.Path("uploads").mkdir(exist_ok=True)
    pathlib.Path("reports").mkdir(exist_ok=True)
    pathlib.Path("static").mkdir(exist_ok=True)
    yield


app = FastAPI(
    title="Combat Analyzer Pro",
    description="Plataforma táctica de análisis para deportes de combate",
    version="2.0.0",
    lifespan=lifespan,
)

# Static files y templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Routers
app.include_router(auth_router)
app.include_router(fighters.router)
app.include_router(fights.router)
app.include_router(analysis.router)
app.include_router(search_router)
app.include_router(chat_router)
app.include_router(pages.router)


# ── Páginas de autenticación ──────────────────────────────────────────────────

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if user:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if user:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/logout")
def logout_page(request: Request, db: Session = Depends(get_db)):
    from fastapi.responses import Response
    token = request.cookies.get(COOKIE_NAME)
    if token:
        db.query(m.UserSession).filter(m.UserSession.token == token).delete()
        db.commit()
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie(COOKIE_NAME)
    return response


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}
