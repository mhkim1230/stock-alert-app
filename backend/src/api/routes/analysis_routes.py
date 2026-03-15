from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import require_session_or_admin
from src.schemas.api import TechnicalAnalysisResponse
from src.services.analysis_service import AnalysisService

router = APIRouter(prefix="/analysis", tags=["analysis"])
analysis_service = AnalysisService()


@router.get(
    "/stocks/{symbol}",
    response_model=TechnicalAnalysisResponse,
    dependencies=[Depends(require_session_or_admin)],
)
async def get_stock_analysis(symbol: str, market: Optional[str] = None):
    analysis = await analysis_service.get_stock_analysis(symbol, market=market)
    if not analysis:
        raise HTTPException(status_code=404, detail="Stock analysis not found")
    return analysis


@router.get(
    "/currencies/{base}/{target}",
    response_model=TechnicalAnalysisResponse,
    dependencies=[Depends(require_session_or_admin)],
)
async def get_currency_analysis(base: str, target: str):
    analysis = await analysis_service.get_currency_analysis(base, target)
    if not analysis:
        raise HTTPException(status_code=404, detail="Currency analysis not found")
    return analysis
