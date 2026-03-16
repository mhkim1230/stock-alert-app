import asyncio

from src.models.database import SessionLocal, init_models
from src.services.watchlist_quote_service import WatchlistQuoteService


async def main() -> None:
    await init_models()
    async with SessionLocal() as db:
        service = WatchlistQuoteService()
        snapshots = await service.refresh_snapshots(db)
        print({"status": "ok", "refreshed": len(snapshots)})


if __name__ == "__main__":
    asyncio.run(main())
