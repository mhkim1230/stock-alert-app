import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import (
    alert_routes,
    auth_routes,
    device_token_routes,
    internal_routes,
    naver_stock_routes,
    news_routes,
    notification_routes,
    watchlist_routes,
)
from src.config.logging_config import configure_logging
from src.config.settings import settings
from src.models.database import init_models

configure_logging()
logger = logging.getLogger(__name__)


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
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(alert_routes.router)
app.include_router(auth_routes.router)
app.include_router(device_token_routes.router)
app.include_router(internal_routes.router)
app.include_router(naver_stock_routes.router)
app.include_router(news_routes.router)
app.include_router(notification_routes.router)
app.include_router(watchlist_routes.router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": "debug" if settings.debug else "production",
    }


@app.get("/")
async def root():
    return {
        "message": "Single-user stock alert API",
        "mode": "admin-key",
        "docs": "/docs" if settings.debug else None,
    }
