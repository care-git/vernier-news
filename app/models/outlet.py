from sqlalchemy import Boolean, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Outlet(Base):
    __tablename__ = "outlets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    country: Mapped[str | None] = mapped_column(String(2))  # ISO 3166-1 alpha-2
    language_primary: Mapped[str | None] = mapped_column(String(10))  # BCP 47
    political_leaning_lr: Mapped[float | None] = mapped_column(Float)  # -1.0 (left) to 1.0 (right)
    political_leaning_source: Mapped[str | None] = mapped_column(String(100))
    parent_org_name: Mapped[str | None] = mapped_column(String(255))
    rss_feed_url: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    articles: Mapped[list["Article"]] = relationship(back_populates="outlet")  # noqa: F821
