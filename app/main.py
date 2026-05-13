"""
Combat Analyzer Pro - Aplicación principal FastAPI.

Servidor: uvicorn app.main:app --reload --port 8000
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.models import db_models  # noqa - registrar modelos
from app.api import fighters, fights, analysis


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: crear tablas si no existen
    Base.metadata.create_all(bind=engine)
    print(f"[startup] {settings.app_name} v{settings.app_version}")
    print(f"[startup] DB: {settings.database_url}")
    print(f"[startup] Uploads: {settings.upload_path}")
    print(f"[startup] Reports: {settings.reports_path}")
    yield
    # Shutdown
    print("[shutdown] OK")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Plataforma profesional de análisis táctico para deportes de combate",
    lifespan=lifespan,
)

# CORS (para desarrollo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Archivos estáticos
app.mount("/static", StaticFiles(directory="/app/static"), name="static")
templates = Jinja2Templates(directory="/app/templates")

# Routers API
app.include_router(fighters.router)
app.include_router(fights.router)
app.include_router(analysis.router)


# ========== FRONTEND (server-rendered) ==========

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/fighters/new", response_class=HTMLResponse)
async def new_fighter_page(request: Request):
    return templates.TemplateResponse("fighter_form.html", {"request": request})


@app.get("/fighters/{fighter_id}", response_class=HTMLResponse)
async def fighter_detail_page(request: Request, fighter_id: int):
    return templates.TemplateResponse(
        "fighter_detail.html",
        {"request": request, "fighter_id": fighter_id},
    )


@app.get("/plan/new", response_class=HTMLResponse)
async def new_plan_page(request: Request):
    return templates.TemplateResponse("plan_new.html", {"request": request})


@app.get("/plan/{plan_id}", response_class=HTMLResponse)
async def plan_detail_page(request: Request, plan_id: int):
    return templates.TemplateResponse(
        "plan_detail.html",
        {"request": request, "plan_id": plan_id},
    )


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }
