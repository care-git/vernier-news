from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import settings

# NullPool prevents connection pool state from being shared across event loops.
# Required because Celery tasks each call asyncio.run(), creating a new event
# loop per task while the engine would otherwise be bound to the import-time loop.
engine = create_async_engine(settings.database_url, echo=settings.app_debug, poolclass=NullPool)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
