import asyncio
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import StockQuoteSnapshot, WatchlistItem
from src.services.stock_service import StockService


class WatchlistQuoteService:
    def __init__(self, stock_service: Optional[StockService] = None) -> None:
        self.stock_service = stock_service or StockService()

    async def list_snapshots(self, db: AsyncSession) -> List[StockQuoteSnapshot]:
        symbols = list(
            (
                await db.execute(
                    select(WatchlistItem.symbol).order_by(WatchlistItem.symbol.asc())
                )
            ).scalars()
        )
        if not symbols:
            return []
        rows = list(
            (
                await db.execute(
                    select(StockQuoteSnapshot).where(StockQuoteSnapshot.symbol.in_(symbols))
                )
            ).scalars()
        )
        row_map = {row.symbol: row for row in rows}
        return [row_map[symbol] for symbol in symbols if symbol in row_map]

    async def refresh_snapshots(
        self,
        db: AsyncSession,
        symbols: Optional[Iterable[str]] = None,
    ) -> List[StockQuoteSnapshot]:
        target_symbols = [symbol.upper() for symbol in (symbols or []) if symbol]
        if not target_symbols:
            target_symbols = list(
                (
                    await db.execute(
                        select(WatchlistItem.symbol).order_by(WatchlistItem.symbol.asc())
                    )
                ).scalars()
            )
        if not target_symbols:
            return []

        quotes = await asyncio.gather(
            *(self.stock_service.get_stock_quote(symbol) for symbol in target_symbols)
        )
        refreshed_symbols: List[str] = []
        for symbol, quote in zip(target_symbols, quotes):
            if not quote or quote.get("price") is None:
                continue

            snapshot = await db.get(StockQuoteSnapshot, symbol)
            if snapshot is None:
                snapshot = StockQuoteSnapshot(
                    symbol=symbol,
                    name=str(quote.get("name") or symbol),
                    market=quote.get("market"),
                    price=float(quote["price"]),
                    change=quote.get("change"),
                    change_percent=quote.get("change_percent"),
                    currency=str(quote.get("currency") or "KRW"),
                    source=str(quote.get("source") or "unknown"),
                    fetched_at=datetime.now(timezone.utc),
                )
                db.add(snapshot)
            else:
                snapshot.name = str(quote.get("name") or snapshot.name or symbol)
                snapshot.market = quote.get("market")
                snapshot.price = float(quote["price"])
                snapshot.change = quote.get("change")
                snapshot.change_percent = quote.get("change_percent")
                snapshot.currency = str(quote.get("currency") or snapshot.currency or "KRW")
                snapshot.source = str(quote.get("source") or snapshot.source or "unknown")
                snapshot.fetched_at = datetime.now(timezone.utc)
            refreshed_symbols.append(symbol)

        await db.commit()
        return await self.list_snapshots_for_symbols(db, refreshed_symbols)

    async def list_snapshots_for_symbols(
        self, db: AsyncSession, symbols: Iterable[str]
    ) -> List[StockQuoteSnapshot]:
        target_symbols = [symbol.upper() for symbol in symbols if symbol]
        if not target_symbols:
            return []
        rows = list(
            (
                await db.execute(
                    select(StockQuoteSnapshot)
                    .where(StockQuoteSnapshot.symbol.in_(target_symbols))
                    .order_by(StockQuoteSnapshot.symbol.asc())
                )
            ).scalars()
        )
        row_map: Dict[str, StockQuoteSnapshot] = {row.symbol: row for row in rows}
        return [row_map[symbol] for symbol in target_symbols if symbol in row_map]

    async def delete_snapshot(self, db: AsyncSession, symbol: str) -> None:
        snapshot = await db.get(StockQuoteSnapshot, symbol.upper())
        if snapshot is not None:
            await db.delete(snapshot)
            await db.commit()
