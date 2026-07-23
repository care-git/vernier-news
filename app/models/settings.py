from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Setting(Base):
    """Typed key/value store for pipeline tuning (clustering, dedup, wire tiers).

    Lets thresholds be calibrated against the live corpus without code changes.
    Values are numeric; the pipeline loads them at task start (see
    ``app/pipeline/tuning.py``) and falls back to code defaults for missing keys.
    """

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str | None] = mapped_column(String(32))
    description: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
