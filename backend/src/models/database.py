import uuid
from datetime import datetime
from typing import AsyncGenerator, Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.config.settings import settings


class Base(DeclarativeBase):
    pass


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


DATABASE_URL = _normalize_database_url(settings.database_url)

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.debug,
    future=True,
    pool_pre_ping=True,
)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class DeviceToken(Base, TimestampMixin):
    __tablename__ = "device_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(20), default="iOS", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class WatchlistItem(Base, TimestampMixin):
    __tablename__ = "watchlist_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)


class FxWatchlistItem(Base, TimestampMixin):
    __tablename__ = "fx_watchlist_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    target_currency: Mapped[str] = mapped_column(String(3), nullable=False, index=True)


class StockAlert(Base, TimestampMixin):
    __tablename__ = "stock_alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    stock_symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    target_price: Mapped[float] = mapped_column(Float, nullable=False)
    condition: Mapped[str] = mapped_column(String(10), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class CurrencyAlert(Base, TimestampMixin):
    __tablename__ = "currency_alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    target_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    target_rate: Mapped[float] = mapped_column(Float, nullable=False)
    condition: Mapped[str] = mapped_column(String(10), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class NewsAlert(Base, TimestampMixin):
    __tablename__ = "news_alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    keywords: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_checked: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    alert_type: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_models() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
