from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.core.config import STATIC_DIR, STATIC_DIR_FALLBACK, settings
from app.core.errors import DomainError
from app.core.logging import configure_logging
from app.routes import files, text

configure_logging()

app = FastAPI(title="Document Anonymization Service")

if settings.cors_allow_origins:
    raw_origins = [item.strip() for item in settings.cors_allow_origins.split(",") if item.strip()]
    allow_all = "*" in raw_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if allow_all else raw_origins,
        allow_credentials=False if allow_all else True,
        allow_methods=["*"] if allow_all else [m.strip() for m in settings.cors_allow_methods.split(",") if m.strip()],
        allow_headers=["*"] if settings.cors_allow_headers == "*" else [h.strip() for h in settings.cors_allow_headers.split(",") if h.strip()],
    )
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Vite build assets
assets_dir = STATIC_DIR / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

app.include_router(text.router)
app.include_router(files.router)


@app.middleware("http")
async def session_middleware(request: Request, call_next):
    session_id = request.cookies.get("anon_session_id")
    if not session_id:
        from uuid import uuid4

        session_id = str(uuid4())
        request.state.session_id = session_id
        response = await call_next(request)
        response.set_cookie("anon_session_id", session_id, httponly=True, samesite="lax")
        return response
    request.state.session_id = session_id
    return await call_next(request)


@app.exception_handler(DomainError)
async def domain_error_handler(_request, exc: DomainError):
    logger.warning("DomainError: {}", exc.message)
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on {} {}", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Внутренняя ошибка сервера"})


@app.get("/")
def index() -> FileResponse:
    if (STATIC_DIR / "index.html").exists():
        return FileResponse(STATIC_DIR / "index.html")
    return FileResponse(STATIC_DIR_FALLBACK / "index.html")
