from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    outlet_id: Mapped[int] = mapped_column(ForeignKey("outlets.id"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(String(10))  # BCP 47
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    author: Mapped[str | None] = mapped_column(String(255))
    collection_source: Mapped[str | None] = mapped_column(String(50))  # rss, api, scrape
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    wire_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    wire_tier: Mapped[int | None] = mapped_column(Integer)  # 0–4; None until computed
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384))

    outlet: Mapped["Outlet"] = relationship(back_populates="articles")  # noqa: F821
    cluster_memberships: Mapped[list["ArticleCluster"]] = relationship(  # noqa: F821
        back_populates="article"
    )
