from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


async def precompute_all_digests(db: AsyncSession) -> int:
    """Build and cache digest payloads for every active user preference profile.

    Returns the number of digests written to Redis.
    """
    ...


async def get_digest(user_id: int) -> dict | None:
    """Return the cached digest for a user, or None if not yet computed."""
    ...
