from sqlalchemy import create_engine, Column, String, Boolean, DateTime, ForeignKey, Numeric, Integer, Float, TIMESTAMP, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.hybrid import hybrid_property
from decimal import Decimal
from datetime import datetime
import uuid
import os
import time
import logging
from typing import Generator, AsyncGenerator
from src.config.settings import settings

# 로거 설정
logger = logging.getLogger(__name__)

# 데이터베이스 URL 가져오기 (클라우드/로컬 자동 감지)
DATABASE_URL = settings.DATABASE_URL or 'sqlite+aiosqlite:///./stock_alert.db'

# PostgreSQL 연결 우선 (Supabase)
is_cloud = os.getenv('RENDER') or os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('HEROKU_APP_ID')
if is_cloud and not DATABASE_URL.startswith('sqlite'):
    # 클라우드 환경에서 PostgreSQL 사용 (asyncpg 드라이버)
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql+asyncpg://', 1)
    elif DATABASE_URL.startswith('postgresql://'):
        DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://', 1)
    db_type = 'PostgreSQL (Supabase + asyncpg)'
elif 'sqlite' in DATABASE_URL:
    # SQLite 설정 (로컬 개발용)
    if not DATABASE_URL.startswith('sqlite+aiosqlite'):
        DATABASE_URL = DATABASE_URL.replace('sqlite:///', 'sqlite+aiosqlite:///')
    db_type = 'SQLite (aiosqlite)'
else:
    db_type = '기타'

logger.info(f"🗄️ 데이터베이스 연결: {db_type}")
logger.info(f"🔗 연결 URL: {DATABASE_URL[:50]}...")

# 비동기 엔진 생성
try:
    if 'postgresql+asyncpg' in DATABASE_URL:
        # PostgreSQL (asyncpg) 설정
        engine = create_async_engine(
            DATABASE_URL,
            echo=settings.DEBUG,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600
        )
    elif 'sqlite+aiosqlite' in DATABASE_URL:
        # SQLite (aiosqlite) 설정
        engine = create_async_engine(
            DATABASE_URL,
            echo=settings.DEBUG,
            pool_pre_ping=True
        )
    else:
        # 기타 데이터베이스
        engine = create_async_engine(DATABASE_URL, echo=settings.DEBUG)
    
    logger.info("✅ 데이터베이스 엔진 생성 완료")
except Exception as e:
    logger.error(f"❌ 데이터베이스 엔진 생성 실패: {e}")
    # 폴백: SQLite 사용
    DATABASE_URL = 'sqlite+aiosqlite:///./stock_alert.db'
    engine = create_async_engine(DATABASE_URL, echo=settings.DEBUG)
    logger.info("🔄 SQLite로 폴백 완료")

# 모델 기본 클래스
Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """비동기 데이터베이스 세션을 생성하고 관리하는 함수"""
    async with AsyncSession(engine) as session:
        try:
            yield session
        finally:
            await session.close()

# 호환성을 위한 AsyncSessionLocal 함수
def AsyncSessionLocal():
    """AsyncSession 생성 함수"""
    return AsyncSession(engine)

# 데이터베이스 객체 생성
database = {
    'engine': engine,
    'AsyncSessionLocal': AsyncSessionLocal,
    'get_db': get_db
}

class User(Base):
    __tablename__ = "USER"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    device_tokens = relationship("DeviceToken", back_populates="user")
    watchlist = relationship("Watchlist", back_populates="user")
    stock_alerts = relationship("StockAlert", back_populates="user")
    currency_alerts = relationship("CurrencyAlert", back_populates="user")
    news_alerts = relationship("NewsAlert", back_populates="user")
    notifications = relationship("NotificationLog", back_populates="user")

class DeviceToken(Base):
    __tablename__ = "DEVICE_TOKEN"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("USER.id"), nullable=False)
    token = Column(String(200), nullable=False)
    device_type = Column(String(20))
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    user = relationship("User", back_populates="device_tokens")

class Watchlist(Base):
    __tablename__ = "WATCHLIST"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("USER.id"), nullable=False)
    symbol = Column(String(20), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    user = relationship("User", back_populates="watchlist")

class StockAlert(Base):
    __tablename__ = "STOCK_ALERT"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("USER.id"), nullable=False)
    stock_symbol = Column(String(20), nullable=False)
    target_price = Column(Numeric(10, 2), nullable=False)
    condition = Column(String(10), nullable=False)  # above, below, equal
    is_active = Column(Numeric(1), default=1)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    triggered_at = Column(TIMESTAMP, nullable=True)
    last_checked = Column(TIMESTAMP, nullable=True)

    user = relationship("User", back_populates="stock_alerts")

    @property
    def target_price_float(self):
        try:
            return float(str(self.target_price)) if self.target_price is not None else None
        except (ValueError, TypeError):
            return None

    @property
    def created_at_iso(self):
        return None if self.created_at is None else self.created_at.isoformat()

    @property
    def triggered_at_iso(self):
        return None if self.triggered_at is None else self.triggered_at.isoformat()

    @property
    def last_checked_iso(self):
        return None if self.last_checked is None else self.last_checked.isoformat()

class CurrencyAlert(Base):
    __tablename__ = "CURRENCY_ALERT"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("USER.id"), nullable=False)
    base_currency = Column(String(3), nullable=False)
    target_currency = Column(String(3), nullable=False)
    target_rate = Column(Numeric(10, 4), nullable=False)
    condition = Column(String(10), nullable=False)  # above, below, equal
    is_active = Column(Numeric(1), default=1)
    triggered_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    user = relationship("User", back_populates="currency_alerts")

class NewsAlert(Base):
    __tablename__ = "NEWS_ALERT"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("USER.id"), nullable=False)
    keywords = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    last_checked = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    user = relationship("User", back_populates="news_alerts")

class NotificationLog(Base):
    __tablename__ = "NOTIFICATION_LOG"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("USER.id"), nullable=False)
    alert_id = Column(String(36), nullable=False)
    alert_type = Column(String(20), nullable=False)  # stock, currency, news
    message = Column(String(500), nullable=False)
    sent_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    status = Column(String(20), nullable=False)  # success, failed
    error_message = Column(String(500), nullable=True)

    user = relationship("User", back_populates="notifications")

async def initialize_database():
    """데이터베이스 초기화"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # 기존 테이블 삭제
        await conn.run_sync(Base.metadata.create_all)  # 새로운 테이블 생성