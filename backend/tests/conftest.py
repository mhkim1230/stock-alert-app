import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

test_database_url = os.environ.get("TEST_DATABASE_URL")
if not test_database_url:
    raise RuntimeError("TEST_DATABASE_URL must point to a hosted PostgreSQL database")
if "sqlite" in test_database_url.lower():
    raise RuntimeError("SQLite/local database is not allowed for tests")

os.environ["DATABASE_URL"] = test_database_url
os.environ["ADMIN_API_KEY"] = os.environ.get("TEST_ADMIN_API_KEY", "test-admin-key")
os.environ["AUTO_CREATE_TABLES"] = "true"

from src.api.main import app
from src.models.database import Base, engine


@pytest_asyncio.fixture(autouse=True)
async def reset_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client


@pytest.fixture
def auth_headers():
    return {"X-Admin-Key": os.environ["ADMIN_API_KEY"]}
