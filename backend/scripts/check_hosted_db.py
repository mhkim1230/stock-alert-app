import asyncio
import os
import sys
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


async def main() -> None:
    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")
    if "sqlite" in database_url.lower():
        raise SystemExit("SQLite/local database URLs are not allowed")
    os.environ.setdefault("ADMIN_API_KEY", "db-check-only")

    from src.models.database import SessionLocal, init_models

    await init_models()

    async with SessionLocal() as session:
        result = await session.execute(text("select current_database(), current_user"))
        row = result.one()
        print(
            {
                "status": "ok",
                "database": row[0],
                "user": row[1],
            }
        )


if __name__ == "__main__":
    asyncio.run(main())
