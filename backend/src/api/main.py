import os
import logging
import asyncio
import json
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

# 라우터 import - 알림 시스템 포함
from src.api.routes import (
    web_simulator_routes,
    naver_stock_routes,
    alert_routes,  # ✅ 알림 라우터 추가
    watchlist_routes  # ✅ 관심종목 라우터 추가
)
from src.config.logging_config import configure_logging
from src.config.settings import settings
from src.services.alert_scheduler import unified_alert_scheduler  # ✅ 스케줄러 추가
from src.models.database import get_db, initialize_database
from src.services.auth_service import AuthService
from src.services.alert_service import AlertService
from src.services.news_service import NewsService
from src.services.stock_service import StockService
from src.services.currency_service import CurrencyService
from src.services.alert_scheduler import AlertScheduler

# 설정 파일 로드
def load_config():
    """설정 파일 로드"""
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {"APP_ENV": "development", "DEBUG": True}

config = load_config()

# 로깅 설정
configure_logging()
logger = logging.getLogger(__name__)

# 📊 애플리케이션 시작 이벤트
@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    logger.info("🚀 주식 알림 API 서버 시작 중...")
    
    # 데이터베이스 테이블 생성
    try:
        from src.models.database import engine, Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ 데이터베이스 테이블 생성/확인 완료")
    except Exception as e:
        logger.error(f"❌ 데이터베이스 테이블 생성 실패: {e}")
        raise
    
    logger.info("🎯 주식 알림 API 서버 시작 완료!")
    yield
    logger.info("🛑 주식 알림 API 서버 종료")

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="주식 알림 API",
    description="실시간 주식/환율 알림 및 뉴스 파싱 시스템",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 웹 시뮬레이터 정적 파일 서빙
web_simulator_path = os.path.join(os.path.dirname(__file__), '..', '..', 'web_simulator')
if os.path.exists(web_simulator_path):
    app.mount("/static", StaticFiles(directory=web_simulator_path), name="static")
    logger.info(f"✅ 웹 시뮬레이터 정적 파일 서빙: {web_simulator_path}")

# 라우터 포함 - 모든 기능 활성화
app.include_router(web_simulator_routes.router, tags=["웹 시뮬레이터"])
app.include_router(naver_stock_routes.router, prefix="/naver", tags=["네이버 실시간 파싱"])
app.include_router(alert_routes.router, tags=["알림 시스템"])  # ✅ 알림 라우터 추가
app.include_router(watchlist_routes.router, tags=["관심종목"])  # ✅ 관심종목 라우터 추가

# 서비스 인스턴스 생성
auth_service = AuthService()
alert_service = AlertService()
news_service = NewsService()
stock_service = StockService()
currency_service = CurrencyService()
alert_scheduler = AlertScheduler(stock_service, currency_service, news_service)

# 웹 시뮬레이터 메인 페이지
@app.get("/", include_in_schema=False)
async def web_simulator():
    """웹 시뮬레이터 메인 페이지"""
    web_simulator_file = os.path.join(web_simulator_path, 'index.html')
    if os.path.exists(web_simulator_file):
        return FileResponse(web_simulator_file)
    else:
        return {"message": "웹 시뮬레이터를 찾을 수 없습니다."}

# Health check 엔드포인트
@app.get("/health", tags=["상태 확인"])
async def health_check():
    """서버 상태 확인"""
    return {
        "status": "healthy",
        "message": "서버가 정상 작동 중입니다.",
        "web_simulator": "available" if os.path.exists(web_simulator_path) else "not_found"
    }

# 기본 상태 확인 엔드포인트
@app.get("/api", tags=["상태 확인"])
async def root():
    """루트 엔드포인트"""
    return {
        "status": "success",
        "message": "주식 알림 시스템 완전판!",
        "features": [
            "✅ 네이버 주식/환율 실시간 파싱",
            "✅ 알림 시스템 (주식, 환율, 뉴스)",
            "✅ 웹 시뮬레이터 연동",
            "✅ 백그라운드 스케줄러"
        ],
        "available_endpoints": [
            "/ - 웹 시뮬레이터",
            "/health - 상태 확인",
            "/naver/stocks/search/엔비디아",
            "/alerts/stock (POST) - 주식 알림 생성",
            "/alerts/currency (POST) - 환율 알림 생성", 
            "/dev/create-test-user (POST) - 테스트 사용자 생성"
        ]
    }

# 개발환경용 간단한 테스트 사용자 생성 엔드포인트
@app.post("/dev/create-test-user")
async def create_test_user(db: AsyncSession = Depends(get_db)):
    """개발환경용 테스트 사용자 생성"""
    try:
        # 테스트 사용자 확인
        test_user = await auth_service.get_user_by_username(db, "testuser")
        if test_user:
            return {"message": "테스트 사용자가 이미 존재합니다", "user_id": str(test_user.id)}
        
        # 새 테스트 사용자 생성
        new_user = await auth_service.register(db, "testuser", "test@example.com", "test123")
        
        # 토큰 생성
        token = await auth_service.authenticate_user(db, str(new_user.username), "test123")
        
        return {
            "message": "테스트 사용자 생성 완료",
            "user_id": str(new_user.id),
            "username": "testuser",
            "token": token,
            "note": "웹 시뮬레이터에서 이 토큰을 사용하세요"
        }
    except Exception as e:
        return {"error": f"테스트 사용자 생성 실패: {str(e)}"}

# 애플리케이션 시작 이벤트
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행되는 이벤트 핸들러"""
    try:
        logger.info("🚀 애플리케이션 시작 - 스케줄러 초기화 중...")
        
        # 데이터베이스 초기화
        await initialize_database()
        logger.info("✅ 데이터베이스 초기화 완료")
        
        # 스케줄러 시작 (백그라운드에서)
        if not unified_alert_scheduler.is_running:
            await unified_alert_scheduler.start()
            logger.info("✅ 백그라운드 알림 스케줄러 시작")
        else:
            logger.info("⚠️ 스케줄러가 이미 실행 중입니다")
            
    except Exception as e:
        logger.error(f"🚨 애플리케이션 시작 중 오류: {str(e)}")
        raise

# 애플리케이션 종료 이벤트
@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 정리 작업"""
    logger.info("🛑 애플리케이션 종료 - 정리 작업 중...")
    try:
        if unified_alert_scheduler.is_running:
            await unified_alert_scheduler.stop()
            logger.info("✅ 스케줄러 정상 종료")
    except Exception as e:
        logger.error(f"❌ 종료 중 오류 발생: {e}")

# 애플리케이션 실행 스크립트
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=False
    ) 