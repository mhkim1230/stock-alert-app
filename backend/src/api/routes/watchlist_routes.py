from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_protected_db
from src.models.database import WatchlistItem
from src.schemas.api import WatchlistItemCreate, WatchlistItemResponse

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.get("", response_model=List[WatchlistItemResponse])
async def list_watchlist(db: AsyncSession = Depends(get_protected_db)):
    items = list((await db.execute(select(WatchlistItem).order_by(WatchlistItem.symbol.asc()))).scalars())
    return items


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


@router.delete("/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watchlist_item(symbol: str, db: AsyncSession = Depends(get_protected_db)):
    item = (await db.execute(select(WatchlistItem).where(WatchlistItem.symbol == symbol.upper()))).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist symbol not found")
    await db.delete(item)
    await db.commit()
