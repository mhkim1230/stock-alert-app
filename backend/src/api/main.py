import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.routes import (
    analysis_routes,
    alert_routes,
    auth_routes,
    device_token_routes,
    internal_routes,
    naver_stock_routes,
    news_routes,
    notification_routes,
    session_routes,
    watchlist_routes,
)
from src.api.dependencies import require_session_or_admin
from src.config.logging_config import configure_logging
from src.config.settings import settings
from src.models.database import init_models

configure_logging()
logger = logging.getLogger(__name__)
STATIC_DIR = Path(__file__).resolve().parents[1] / "web"


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.auto_create_tables:
        await init_models()
        logger.info("Database tables ensured")
    yield


app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(session_routes.router)
app.include_router(analysis_routes.router)
app.include_router(alert_routes.router)
app.include_router(auth_routes.router)
app.include_router(device_token_routes.router)
app.include_router(internal_routes.router)
app.include_router(naver_stock_routes.router)
app.include_router(news_routes.router)
app.include_router(notification_routes.router)
app.include_router(watchlist_routes.router)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR / "static"), name="static")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": "debug" if settings.debug else "production",
    }


@app.get("/")
async def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/design-samples")
async def design_samples():
    return FileResponse(STATIC_DIR / "design-samples.html")


@app.get("/manifest.webmanifest")
async def manifest():
    return FileResponse(STATIC_DIR / "manifest.webmanifest", media_type="application/manifest+json")


@app.get("/sw.js")
async def service_worker():
    return FileResponse(STATIC_DIR / "sw.js", media_type="application/javascript")


@app.get("/app-bootstrap")
async def app_bootstrap(_: None = Depends(require_session_or_admin)):
    return {"status": "ok"}
