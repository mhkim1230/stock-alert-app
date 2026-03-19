import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.models.database import SessionLocal
from src.services.fx_watchlist_quote_service import FxWatchlistQuoteService


async def main() -> None:
    service = FxWatchlistQuoteService()
    async with SessionLocal() as session:
        snapshots = await service.refresh_snapshots(session)
        print(f"refreshed_fx_snapshots={len(snapshots)}")


if __name__ == "__main__":
    asyncio.run(main())
