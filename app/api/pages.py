"""
Páginas server-rendered (frontend).

Extraído de app/main.py para que main.py (con autenticación) pueda
incluirlo como router: `app.include_router(pages.router)`.
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/fighters/new", response_class=HTMLResponse)
async def new_fighter_page(request: Request):
    return templates.TemplateResponse("fighter_form.html", {"request": request})


@router.get("/fighters/{fighter_id}", response_class=HTMLResponse)
async def fighter_detail_page(request: Request, fighter_id: int):
    return templates.TemplateResponse(
        "fighter_detail.html",
        {"request": request, "fighter_id": fighter_id},
    )


@router.get("/plan/new", response_class=HTMLResponse)
async def new_plan_page(request: Request):
    return templates.TemplateResponse("plan_new.html", {"request": request})


@router.get("/plan/{plan_id}", response_class=HTMLResponse)
async def plan_detail_page(request: Request, plan_id: int):
    return templates.TemplateResponse(
        "plan_detail.html",
        {"request": request, "plan_id": plan_id},
    )
