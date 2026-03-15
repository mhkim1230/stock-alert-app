from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import require_session_or_admin
from src.schemas.api import ExchangeRateResponse, SearchStocksResponse, StockQuoteResponse
from src.services.currency_service import CurrencyService
from src.services.stock_service import StockService

router = APIRouter(tags=["market"])
stock_service = StockService()
currency_service = CurrencyService()


@router.get("/stocks/search", response_model=SearchStocksResponse, dependencies=[Depends(require_session_or_admin)])
async def search_stocks(query: str):
    return {"results": await stock_service.search_stocks(query)}


@router.get("/stocks/{symbol}", response_model=StockQuoteResponse, dependencies=[Depends(require_session_or_admin)])
async def get_stock(symbol: str):
    quote = await stock_service.get_stock_quote(symbol)
    if not quote:
        raise HTTPException(status_code=404, detail="Stock quote not found")
    return quote


@router.get("/currency/rate", response_model=ExchangeRateResponse, dependencies=[Depends(require_session_or_admin)])
async def get_exchange_rate(base: str, target: str):
    rate = await currency_service.get_exchange_rate(base, target)
    if not rate:
        raise HTTPException(status_code=404, detail="Exchange rate not found")
    return rate
