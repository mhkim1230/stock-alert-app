from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from pydantic import validator
from decimal import Decimal
import uuid
from sqlalchemy import select
from fastapi.responses import JSONResponse
import logging

from src.services.auth_service import get_current_user
from src.services.alert_scheduler import unified_alert_scheduler
from src.models.database import User, StockAlert, CurrencyAlert, NewsAlert, get_db
from src.services.naver_stock_service import NaverStockService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["Alerts"])

class StockAlertCreate(BaseModel):
    """주식 알림 생성 요청 모델"""
    stock_symbol: str = Field(..., description="주식 심볼 (예: AAPL)")
    target_price: Optional[float] = Field(None, gt=0, description="목표 가격")
    percentage_change: Optional[float] = Field(None, description="목표 가격 변화율 (%)")
    condition: str = Field(..., pattern="^(above|below|equal)$", description="알림 조건")

    @validator('target_price', 'percentage_change')
    def validate_price_or_percentage(cls, v, values):
        if 'target_price' in values and 'percentage_change' in values:
            if values['target_price'] is None and values['percentage_change'] is None:
                raise ValueError("목표 가격 또는 변화율 중 하나는 반드시 지정해야 합니다.")
            if values['target_price'] is not None and values['percentage_change'] is not None:
                raise ValueError("목표 가격과 변화율은 동시에 지정할 수 없습니다.")
        return v

class CurrencyAlertCreate(BaseModel):
    """환율 알림 생성 요청 모델"""
    base_currency: str = Field(..., min_length=3, max_length=3, description="기준 통화")
    target_currency: str = Field(..., min_length=3, max_length=3, description="대상 통화")
    target_rate: float = Field(..., gt=0, description="목표 환율")
    condition: str = Field(..., pattern="^(above|below|equal)$", description="알림 조건")

class NewsAlertCreate(BaseModel):
    """뉴스 알림 생성 요청 모델"""
    keywords: str = Field(..., description="키워드 (쉼표로 구분)")

class AlertResponse(BaseModel):
    """알림 응답 모델"""
    id: int
    is_active: bool
    created_at: datetime
    triggered_at: Optional[datetime] = None

class StockAlertResponse(AlertResponse):
    """주식 알림 응답 모델"""
    stock_symbol: str
    target_price: float
    percentage_change: Optional[float] = None
    calculated_price: Optional[float] = None
    condition: str

class CurrencyAlertResponse(AlertResponse):
    """환율 알림 응답 모델"""
    base_currency: str
    target_currency: str
    target_rate: float
    condition: str

class NewsAlertResponse(AlertResponse):
    """뉴스 알림 응답 모델"""
    keywords: str
    last_checked: Optional[datetime] = None

# 주식 알림 관리
@router.post("/stock", response_model=StockAlertResponse)
async def create_stock_alert(
    alert_data: StockAlertCreate,
    current_user: User = Depends(get_current_user)
):
    """주식 알림 생성"""
    try:
        # 사용자의 활성 주식 알림 개수 확인
        active_count = StockAlert.select().where(
            (StockAlert.user == current_user.id) & 
            (StockAlert.is_active == True)
        ).count()
        
        if active_count >= 10:  # 최대 10개 제한
            raise HTTPException(
                status_code=400,
                detail="최대 10개의 주식 알림만 생성할 수 있습니다."
            )
        
        # 현재 주가 조회
        stock_service = NaverStockService()
        current_price = await stock_service.get_stock_price(alert_data.stock_symbol)
        
        if current_price is None:
            raise HTTPException(
                status_code=400,
                detail="현재 주가를 조회할 수 없습니다."
            )
        
        # 목표가 계산
        target_price = alert_data.target_price
        percentage_change = alert_data.percentage_change
        calculated_price = None
        
        if percentage_change is not None:
            calculated_price = current_price * (1 + percentage_change / 100)
            target_price = calculated_price
        
        # 새 알림 생성
        new_alert = StockAlert.create(
            user=current_user.id,
            stock_symbol=alert_data.stock_symbol.upper(),
            target_price=target_price,
            percentage_change=percentage_change,
            calculated_price=calculated_price,
            condition=alert_data.condition,
            is_active=True
        )
        
        created_at_value = new_alert.created_at.scalar() if hasattr(new_alert.created_at, 'scalar') else new_alert.created_at
        triggered_at_value = new_alert.triggered_at.scalar() if hasattr(new_alert.triggered_at, 'scalar') else new_alert.triggered_at
        
        return StockAlertResponse(
            id=new_alert.id,
            stock_symbol=new_alert.stock_symbol,
            target_price=new_alert.target_price,
            percentage_change=new_alert.percentage_change,
            calculated_price=new_alert.calculated_price,
            condition=new_alert.condition,
            is_active=new_alert.is_active,
            created_at=created_at_value,
            triggered_at=triggered_at_value
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"주식 알림 생성 중 오류 발생: {str(e)}"
        )

@router.get("/stock", response_model=List[StockAlertResponse])
async def get_stock_alerts(
    current_user: User = Depends(get_current_user)
):
    """사용자의 주식 알림 목록 조회"""
    try:
        alerts = list(StockAlert.select().where(StockAlert.user == current_user.id))
        
        return [
            StockAlertResponse(
                id=alert.id,
                stock_symbol=alert.stock_symbol,
                target_price=alert.target_price,
                percentage_change=alert.percentage_change,
                calculated_price=alert.calculated_price,
                condition=alert.condition,
                is_active=alert.is_active,
                created_at=alert.created_at.scalar() if hasattr(alert.created_at, 'scalar') else alert.created_at,
                triggered_at=alert.triggered_at.scalar() if hasattr(alert.triggered_at, 'scalar') else alert.triggered_at
            )
            for alert in alerts
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"주식 알림 조회 중 오류 발생: {str(e)}"
        )

@router.delete("/stock/{alert_id}")
async def delete_stock_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user)
):
    """주식 알림 삭제"""
    try:
        alert = StockAlert.select().where(
            (StockAlert.id == alert_id) & 
            (StockAlert.user == current_user.id)
        ).first()
        
        if not alert:
            raise HTTPException(
                status_code=404,
                detail="알림을 찾을 수 없습니다."
            )
        
        alert.delete_instance()
        
        return {"message": "주식 알림이 성공적으로 삭제되었습니다."}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"주식 알림 삭제 중 오류 발생: {str(e)}"
        )

# 환율 알림 관리
@router.post("/currency", response_model=CurrencyAlertResponse)
async def create_currency_alert(
    alert_data: CurrencyAlertCreate,
    current_user: User = Depends(get_current_user)
):
    """환율 알림 생성"""
    try:
        # 사용자의 활성 환율 알림 개수 확인
        active_count = CurrencyAlert.select().where(
            (CurrencyAlert.user == current_user.id) & 
            (CurrencyAlert.is_active == True)
        ).count()
        
        if active_count >= 10:  # 최대 10개 제한
            raise HTTPException(
                status_code=400,
                detail="최대 10개의 환율 알림만 생성할 수 있습니다."
            )
        
        # 새 알림 생성
        new_alert = CurrencyAlert.create(
            user=current_user.id,
            base_currency=alert_data.base_currency.upper(),
            target_currency=alert_data.target_currency.upper(),
            target_rate=alert_data.target_rate,
            condition=alert_data.condition,
            is_active=True
        )
        
        created_at_value = new_alert.created_at.scalar() if hasattr(new_alert.created_at, 'scalar') else new_alert.created_at
        triggered_at_value = new_alert.triggered_at.scalar() if hasattr(new_alert.triggered_at, 'scalar') else new_alert.triggered_at
        
        return CurrencyAlertResponse(
            id=new_alert.id,
            base_currency=new_alert.base_currency,
            target_currency=new_alert.target_currency,
            target_rate=new_alert.target_rate,
            condition=new_alert.condition,
            is_active=new_alert.is_active,
            created_at=created_at_value,
            triggered_at=triggered_at_value
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"환율 알림 생성 중 오류 발생: {str(e)}"
        )

@router.get("/currency", response_model=List[CurrencyAlertResponse])
async def get_currency_alerts(
    current_user: User = Depends(get_current_user)
):
    """사용자의 환율 알림 목록 조회"""
    try:
        alerts = list(CurrencyAlert.select().where(CurrencyAlert.user == current_user.id))
        
        return [
            CurrencyAlertResponse(
                id=alert.id,
                base_currency=alert.base_currency,
                target_currency=alert.target_currency,
                target_rate=alert.target_rate,
                condition=alert.condition,
                is_active=alert.is_active,
                created_at=alert.created_at.scalar() if hasattr(alert.created_at, 'scalar') else alert.created_at,
                triggered_at=alert.triggered_at.scalar() if hasattr(alert.triggered_at, 'scalar') else alert.triggered_at
            )
            for alert in alerts
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"환율 알림 조회 중 오류 발생: {str(e)}"
        )

@router.delete("/currency/{alert_id}")
async def delete_currency_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user)
):
    """환율 알림 삭제"""
    try:
        alert = CurrencyAlert.select().where(
            (CurrencyAlert.id == alert_id) & 
            (CurrencyAlert.user == current_user.id)
        ).first()
        
        if not alert:
            raise HTTPException(
                status_code=404,
                detail="알림을 찾을 수 없습니다."
            )
        
        alert.delete_instance()
        
        return {"message": "환율 알림이 성공적으로 삭제되었습니다."}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"환율 알림 삭제 중 오류 발생: {str(e)}"
        )

# 뉴스 알림 관리
@router.post("/news", response_model=NewsAlertResponse)
async def create_news_alert(
    alert_data: NewsAlertCreate,
    current_user: User = Depends(get_current_user)
):
    """뉴스 알림 생성"""
    try:
        # 사용자의 활성 뉴스 알림 개수 확인
        active_count = NewsAlert.select().where(
            (NewsAlert.user == current_user.id) & 
            (NewsAlert.is_active == True)
        ).count()
        
        if active_count >= 5:  # 최대 5개 제한
            raise HTTPException(
                status_code=400,
                detail="최대 5개의 뉴스 알림만 생성할 수 있습니다."
            )
        
        # 새 알림 생성
        new_alert = NewsAlert.create(
            user=current_user.id,
            keywords=alert_data.keywords,
            is_active=True
        )
        
        created_at_value = new_alert.created_at.scalar() if hasattr(new_alert.created_at, 'scalar') else new_alert.created_at
        triggered_at_value = new_alert.triggered_at.scalar() if hasattr(new_alert.triggered_at, 'scalar') else new_alert.triggered_at
        
        return NewsAlertResponse(
            id=new_alert.id,
            keywords=new_alert.keywords,
            is_active=new_alert.is_active,
            created_at=created_at_value,
            last_checked=triggered_at_value
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"뉴스 알림 생성 중 오류 발생: {str(e)}"
        )

@router.get("/news", response_model=List[NewsAlertResponse])
async def get_news_alerts(
    current_user: User = Depends(get_current_user)
):
    """사용자의 뉴스 알림 목록 조회"""
    try:
        alerts = list(NewsAlert.select().where(NewsAlert.user == current_user.id))
        
        return [
            NewsAlertResponse(
                id=alert.id,
                keywords=alert.keywords,
                is_active=alert.is_active,
                created_at=alert.created_at.scalar() if hasattr(alert.created_at, 'scalar') else alert.created_at,
                last_checked=alert.triggered_at.scalar() if hasattr(alert.triggered_at, 'scalar') else alert.triggered_at
            )
            for alert in alerts
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"뉴스 알림 조회 중 오류 발생: {str(e)}"
        )

@router.delete("/news/{alert_id}")
async def delete_news_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user)
):
    """뉴스 알림 삭제"""
    try:
        alert = NewsAlert.select().where(
            (NewsAlert.id == alert_id) & 
            (NewsAlert.user == current_user.id)
        ).first()
        
        if not alert:
            raise HTTPException(
                status_code=404,
                detail="알림을 찾을 수 없습니다."
            )
        
        alert.delete_instance()
        
        return {"message": "뉴스 알림이 성공적으로 삭제되었습니다."}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"뉴스 알림 삭제 중 오류 발생: {str(e)}"
        )

# 스케줄러 상태 조회
@router.get("/scheduler/status")
async def get_scheduler_status(
    current_user: User = Depends(get_current_user)
):
    """알림 스케줄러 상태 조회"""
    try:
        status = await unified_alert_scheduler.get_scheduler_status()
        return status
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"스케줄러 상태 조회 중 오류 발생: {str(e)}"
        )

# 🧪 개발용 인증 없는 알람 엔드포인트
@router.post("/test/stock")
async def create_test_stock_alert(alert_data: StockAlertCreate):
    """테스트용 주식 알림 생성"""
    try:
        # 테스트 데이터 검증
        if not alert_data.stock_symbol:
            raise ValueError("주식 심볼이 필요합니다")
        
        if not alert_data.condition:
            raise ValueError("알림 조건이 필요합니다")
        
        if not alert_data.target_price and not alert_data.percentage_change:
            raise ValueError("목표 가격 또는 변화율이 필요합니다")

        # 응답 데이터 생성
        response_data = {
            "id": 1,
            "stock_symbol": alert_data.stock_symbol,
            "target_price": alert_data.target_price,
            "percentage_change": alert_data.percentage_change,
            "condition": alert_data.condition,
            "is_active": True,
            "created_at": datetime.now(),
            "triggered_at": None
        }

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status": "success",
                "message": "테스트 알림이 생성되었습니다",
                "data": response_data
            }
        )

    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status": "error",
                "message": str(e),
                "error_type": "validation_error"
            }
        )
    except Exception as e:
        logger.error(f"테스트 알림 생성 중 오류: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "내부 서버 오류가 발생했습니다",
                "error_type": "internal_server_error"
            }
        )

@router.post("/test/currency")
async def create_test_currency_alert(alert_data: CurrencyAlertCreate):
    """개발용 환율 알림 생성 (인증 없음)"""
    try:
        # 테스트 사용자 ID 고정 (ID: 1)
        test_user_id = 1
        
        # 새 알림 생성
        new_alert = CurrencyAlert.create(
            user=test_user_id,
            base_currency=alert_data.base_currency.upper(),
            target_currency=alert_data.target_currency.upper(),
            target_rate=alert_data.target_rate,
            condition=alert_data.condition,
            is_active=True
        )
        
        created_at_value = new_alert.created_at.scalar() if hasattr(new_alert.created_at, 'scalar') else new_alert.created_at
        triggered_at_value = new_alert.triggered_at.scalar() if hasattr(new_alert.triggered_at, 'scalar') else new_alert.triggered_at
        
        return {
            "id": new_alert.id,
            "base_currency": new_alert.base_currency,
            "target_currency": new_alert.target_currency,
            "target_rate": new_alert.target_rate,
            "condition": new_alert.condition,
            "is_active": new_alert.is_active,
            "created_at": created_at_value.isoformat() if created_at_value else None,
            "triggered_at": triggered_at_value.isoformat() if triggered_at_value else None,
            "last_checked": new_alert.last_checked.scalar().isoformat() if hasattr(new_alert.last_checked, 'scalar') else new_alert.last_checked.isoformat() if new_alert.last_checked else None,
            "message": "✅ 테스트 환율 알람 생성 완료 (데이터베이스 저장됨)"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"테스트 환율 알림 생성 중 오류 발생: {str(e)}"
        )

@router.get("/test/stock")
async def get_test_stock_alerts():
    """테스트용 주식 알림 목록 조회"""
    try:
        # 테스트 데이터 생성
        test_alerts = [
            {
                "id": 1,
                "stock_symbol": "005930",  # 삼성전자
                "target_price": 70000,
                "condition": "above",
                "is_active": True,
                "created_at": datetime.now(),
                "triggered_at": None
            },
            {
                "id": 2,
                "stock_symbol": "066570",  # LG전자
                "target_price": 80000,
                "condition": "below",
                "is_active": True,
                "created_at": datetime.now(),
                "triggered_at": None
            }
        ]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "테스트 알림 목록을 조회했습니다",
                "data": test_alerts
            }
        )

    except Exception as e:
        logger.error(f"테스트 알림 목록 조회 중 오류: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "내부 서버 오류가 발생했습니다",
                "error_type": "internal_server_error"
            }
        ) 