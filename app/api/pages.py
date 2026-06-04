"""
Páginas server-rendered (frontend).

Extraído de app/main.py para que main.py (con autenticación) pueda
incluirlo como router: `app.include_router(pages.router)`.
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.auth import get_current_user_optional

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="templates")


def _require_login(request: Request, db: Session):
    """Devuelve el usuario o None. Las páginas redirigen a /login si es None."""
    return get_current_user_optional(request, db)


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    if not _require_login(request, db):
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/fighters/new", response_class=HTMLResponse)
async def new_fighter_page(request: Request, db: Session = Depends(get_db)):
    if not _require_login(request, db):
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("fighter_form.html", {"request": request})


@router.get("/fighters/{fighter_id}", response_class=HTMLResponse)
async def fighter_detail_page(request: Request, fighter_id: int, db: Session = Depends(get_db)):
    if not _require_login(request, db):
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse(
        "fighter_detail.html",
        {"request": request, "fighter_id": fighter_id},
    )


@router.get("/plan/new", response_class=HTMLResponse)
async def new_plan_page(request: Request, db: Session = Depends(get_db)):
    if not _require_login(request, db):
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("plan_new.html", {"request": request})


@router.get("/plan/{plan_id}", response_class=HTMLResponse)
async def plan_detail_page(request: Request, plan_id: int, db: Session = Depends(get_db)):
    if not _require_login(request, db):
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse(
        "plan_detail.html",
        {"request": request, "plan_id": plan_id},
    )
