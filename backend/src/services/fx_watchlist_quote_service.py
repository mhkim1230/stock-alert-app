from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import FxRateSnapshot, FxWatchlistItem
from src.services.currency_service import CurrencyService


class FxWatchlistQuoteService:
    def __init__(self, currency_service: Optional[CurrencyService] = None) -> None:
        self.currency_service = currency_service or CurrencyService()

    async def list_snapshots(self, db: AsyncSession) -> List[FxRateSnapshot]:
        pairs = list(
            (
                await db.execute(
                    select(FxWatchlistItem.base_currency, FxWatchlistItem.target_currency).order_by(
                        FxWatchlistItem.base_currency.asc(),
                        FxWatchlistItem.target_currency.asc(),
                    )
                )
            ).all()
        )
        if not pairs:
            return []

        keys = [self._pair_key(base, target) for base, target in pairs]
        rows = list(
            (
                await db.execute(
                    select(FxRateSnapshot).where(FxRateSnapshot.pair_key.in_(keys))
                )
            ).scalars()
        )
        row_map = {row.pair_key: row for row in rows}
        return [row_map[key] for key in keys if key in row_map]

    async def refresh_snapshots(
        self,
        db: AsyncSession,
        pairs: Optional[Iterable[str]] = None,
    ) -> List[FxRateSnapshot]:
        target_pairs = self._normalize_pair_keys(pairs or [])
        if not target_pairs:
            target_pairs = [
                self._pair_key(base, target)
                for base, target in (
                    await db.execute(
                        select(FxWatchlistItem.base_currency, FxWatchlistItem.target_currency).order_by(
                            FxWatchlistItem.base_currency.asc(),
                            FxWatchlistItem.target_currency.asc(),
                        )
                    )
                ).all()
            ]
        if not target_pairs:
            return []

        refreshed: List[str] = []
        for pair_key in target_pairs:
            base, target = self._split_pair_key(pair_key)
            payload = await self.currency_service.get_exchange_rate(base, target)
            if not payload or payload.get("rate") is None:
                continue

            snapshot = await db.get(FxRateSnapshot, pair_key)
            if snapshot is None:
                snapshot = FxRateSnapshot(
                    pair_key=pair_key,
                    base_currency=base,
                    target_currency=target,
                    rate=float(payload["rate"]),
                    source=str(payload.get("source") or "unknown"),
                    fetched_at=datetime.now(timezone.utc),
                )
                db.add(snapshot)
            else:
                snapshot.rate = float(payload["rate"])
                snapshot.source = str(payload.get("source") or snapshot.source or "unknown")
                snapshot.fetched_at = datetime.now(timezone.utc)
            refreshed.append(pair_key)

        await db.commit()
        return await self.list_snapshots_for_pairs(db, refreshed)

    async def list_snapshots_for_pairs(
        self,
        db: AsyncSession,
        pairs: Iterable[str],
    ) -> List[FxRateSnapshot]:
        keys = self._normalize_pair_keys(pairs)
        if not keys:
            return []
        rows = list(
            (
                await db.execute(
                    select(FxRateSnapshot)
                    .where(FxRateSnapshot.pair_key.in_(keys))
                    .order_by(FxRateSnapshot.pair_key.asc())
                )
            ).scalars()
        )
        row_map: Dict[str, FxRateSnapshot] = {row.pair_key: row for row in rows}
        return [row_map[key] for key in keys if key in row_map]

    async def delete_snapshot(self, db: AsyncSession, base: str, target: str) -> None:
        pair_key = self._pair_key(base, target)
        snapshot = await db.get(FxRateSnapshot, pair_key)
        if snapshot is not None:
            await db.delete(snapshot)
            await db.commit()

    @staticmethod
    def _pair_key(base: str, target: str) -> str:
        return f"{base.upper()}/{target.upper()}"

    @staticmethod
    def _split_pair_key(pair_key: str) -> Tuple[str, str]:
        base, target = pair_key.split("/", 1)
        return base.upper(), target.upper()

    def _normalize_pair_keys(self, pairs: Iterable[str]) -> List[str]:
        normalized: List[str] = []
        for pair in pairs:
            text = str(pair or "").strip().upper()
            if "/" in text:
                base, target = self._split_pair_key(text)
            elif len(text) == 6:
                base, target = text[:3], text[3:]
            else:
                continue
            normalized.append(self._pair_key(base, target))
        return normalized
