from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import EMBEDDING_DIM
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
    collection_source: Mapped[str | None] = mapped_column(Text)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    wire_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    wire_tier: Mapped[int | None] = mapped_column(Integer)  # 0–4; None until computed
    # None = a normal story article, the only kind that gets story-clustered.
    # See app/pipeline/dedup.py and migration 0009.
    content_type: Mapped[str | None] = mapped_column(String(32))
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))

    outlet: Mapped["Outlet"] = relationship(back_populates="articles")  # noqa: F821
    cluster_memberships: Mapped[list["ArticleCluster"]] = relationship(  # noqa: F821
        back_populates="article"
    )
    sightings: Mapped[list["ArticleSighting"]] = relationship(back_populates="article")
    mentions: Mapped[list["EntityMention"]] = relationship(back_populates="article")  # noqa: F821


class ArticleSighting(Base):
    """Every URL form and collection path one article arrived under.

    The Article row keeps whichever form was seen first; the rest would otherwise be
    discarded. How a story propagates across paths and collection methods is research
    data in its own right — see migration 0010 and docs/data-model.md.
    """

    __tablename__ = "article_sightings"
    __table_args__ = (
        UniqueConstraint("article_id", "url", name="uq_article_sightings_article_url"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    collection_source: Mapped[str | None] = mapped_column(Text)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    article: Mapped["Article"] = relationship(back_populates="sightings")
