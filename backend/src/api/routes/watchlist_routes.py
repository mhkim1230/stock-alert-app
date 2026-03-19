from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_protected_db
from src.models.database import FxWatchlistItem, WatchlistItem
from src.schemas.api import (
    FxWatchlistItemCreate,
    FxRateSnapshotResponse,
    FxWatchlistItemResponse,
    FxWatchlistQuotesRefreshRequest,
    StockQuoteSnapshotResponse,
    WatchlistItemCreate,
    WatchlistItemResponse,
    WatchlistQuotesRefreshRequest,
)
from src.services.fx_watchlist_quote_service import FxWatchlistQuoteService
from src.services.watchlist_quote_service import WatchlistQuoteService

router = APIRouter(prefix="/watchlist", tags=["watchlist"])
watchlist_quote_service = WatchlistQuoteService()
fx_watchlist_quote_service = FxWatchlistQuoteService()


@router.get("", response_model=List[WatchlistItemResponse])
async def list_watchlist(db: AsyncSession = Depends(get_protected_db)):
    items = list((await db.execute(select(WatchlistItem).order_by(WatchlistItem.symbol.asc()))).scalars())
    return items


@router.get("/fx", response_model=List[FxWatchlistItemResponse])
async def list_fx_watchlist(db: AsyncSession = Depends(get_protected_db)):
    items = list(
        (
            await db.execute(
                select(FxWatchlistItem).order_by(
                    FxWatchlistItem.base_currency.asc(),
                    FxWatchlistItem.target_currency.asc(),
                )
            )
        ).scalars()
    )
    return items


@router.get("/quotes", response_model=List[StockQuoteSnapshotResponse])
async def list_watchlist_quotes(db: AsyncSession = Depends(get_protected_db)):
    return await watchlist_quote_service.list_snapshots(db)


@router.get("/fx/quotes", response_model=List[FxRateSnapshotResponse])
async def list_fx_watchlist_quotes(db: AsyncSession = Depends(get_protected_db)):
    return await fx_watchlist_quote_service.list_snapshots(db)


@router.post("", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED)
async def create_watchlist_item(payload: WatchlistItemCreate, db: AsyncSession = Depends(get_protected_db)):
    symbol = payload.symbol.upper()
    existing = (await db.execute(select(WatchlistItem).where(WatchlistItem.symbol == symbol))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Symbol already exists in watchlist")
    item = WatchlistItem(symbol=symbol)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/fx", response_model=FxWatchlistItemResponse, status_code=status.HTTP_201_CREATED)
async def create_fx_watchlist_item(
    payload: FxWatchlistItemCreate, db: AsyncSession = Depends(get_protected_db)
):
    base_currency = payload.base_currency.upper()
    target_currency = payload.target_currency.upper()
    existing = (
        await db.execute(
            select(FxWatchlistItem).where(
                FxWatchlistItem.base_currency == base_currency,
                FxWatchlistItem.target_currency == target_currency,
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Currency pair already exists in watchlist")

    item = FxWatchlistItem(base_currency=base_currency, target_currency=target_currency)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/quotes/refresh", response_model=List[StockQuoteSnapshotResponse])
async def refresh_watchlist_quotes(
    payload: WatchlistQuotesRefreshRequest, db: AsyncSession = Depends(get_protected_db)
):
    return await watchlist_quote_service.refresh_snapshots(db, payload.symbols)


@router.post("/fx/quotes/refresh", response_model=List[FxRateSnapshotResponse])
async def refresh_fx_watchlist_quotes(
    payload: FxWatchlistQuotesRefreshRequest, db: AsyncSession = Depends(get_protected_db)
):
    return await fx_watchlist_quote_service.refresh_snapshots(db, payload.pairs)


@router.delete("/fx/{base_currency}/{target_currency}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fx_watchlist_item(
    base_currency: str, target_currency: str, db: AsyncSession = Depends(get_protected_db)
):
    item = (
        await db.execute(
            select(FxWatchlistItem).where(
                FxWatchlistItem.base_currency == base_currency.upper(),
                FxWatchlistItem.target_currency == target_currency.upper(),
            )
        )
    ).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="FX watchlist pair not found")
    await db.delete(item)
    await db.commit()
    await fx_watchlist_quote_service.delete_snapshot(db, base_currency.upper(), target_currency.upper())


@router.delete("/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watchlist_item(symbol: str, db: AsyncSession = Depends(get_protected_db)):
    item = (await db.execute(select(WatchlistItem).where(WatchlistItem.symbol == symbol.upper()))).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist symbol not found")
    await db.delete(item)
    await db.commit()
    await watchlist_quote_service.delete_snapshot(db, symbol.upper())
