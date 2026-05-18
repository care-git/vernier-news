from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Cluster(Base):
    __tablename__ = "clusters"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    total_source_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    independent_source_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    category: Mapped["Category"] = relationship(back_populates="clusters")  # noqa: F821
    article_memberships: Mapped[list["ArticleCluster"]] = relationship(back_populates="cluster")


class ArticleCluster(Base):
    __tablename__ = "article_cluster"

    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), primary_key=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("clusters.id"), primary_key=True)
    independence_score: Mapped[float] = mapped_column(Float, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    article: Mapped["Article"] = relationship(back_populates="cluster_memberships")  # noqa: F821
    cluster: Mapped["Cluster"] = relationship(back_populates="article_memberships")
