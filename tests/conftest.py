import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "postgresql+asyncpg://vernier:changeme@localhost:5432/vernier_news_test"

# NullPool: no connection pooling — each checkout opens a fresh asyncpg connection
# in the caller's event loop. Required for pytest-asyncio where each test runs in
# its own function-scoped event loop.
engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Create the test schema once before all tests and drop it after.

    Intentionally synchronous — uses asyncio.run() internally so it runs in its
    own isolated event loop that is fully closed before any test loop starts.
    This avoids cross-loop asyncpg Future errors when pytest-asyncio gives each
    test its own function-scoped loop.
    """

    async def _create() -> None:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(Base.metadata.create_all)

    async def _drop() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    asyncio.run(_create())
    yield
    asyncio.run(_drop())


@pytest.fixture
async def db() -> AsyncSession:
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
async def client(db: AsyncSession) -> AsyncClient:
    app.dependency_overrides[get_db] = lambda: db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
