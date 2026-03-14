from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_protected_db
from src.config.settings import settings
from src.schemas.api import InternalRunResponse
from src.services.alert_service import AlertService
from src.services.currency_service import CurrencyService
from src.services.news_service import NewsService
from src.services.notification_service import NotificationService
from src.services.stock_service import StockService

router = APIRouter(prefix="/internal", tags=["internal"])
alert_service = AlertService(
    stock_service=StockService(),
    currency_service=CurrencyService(),
    news_service=NewsService(),
    notification_service=NotificationService(settings),
)


@router.post("/run-alert-checks", response_model=InternalRunResponse)
async def run_alert_checks(db: AsyncSession = Depends(get_protected_db)):
    result = await alert_service.run_checks(db)
    return {"status": "ok", **result}
