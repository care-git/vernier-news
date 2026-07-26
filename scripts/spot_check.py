"""Qualitative spot-check of clustering — print real clusters and singletons so we
can eyeball whether same-story grouping actually works (numbers alone can't say).

    make spotcheck
    # docker compose exec api python -m scripts.spot_check

Read-only. Samples are random each run, so run it a few times for a feel.
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select, text

from app.database import SessionLocal
from app.models.article import Article
from app.models.cluster import ArticleCluster
from app.models.outlet import Outlet

_N = 6  # clusters shown per section


def _hr(title: str) -> None:
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


async def _members(db, cluster_id):
    return (
        await db.execute(
            select(Outlet.name, Article.title, Article.published_at)
            .join(ArticleCluster, ArticleCluster.article_id == Article.id)
            .join(Outlet, Outlet.id == Article.outlet_id)
            .where(ArticleCluster.cluster_id == cluster_id)
            .order_by(Article.published_at.asc())
        )
    ).all()


def _print_members(rows, cap: int = 10) -> None:
    for r in rows[:cap]:
        day = r.published_at.strftime("%Y-%m-%d") if r.published_at else "----------"
        title = " ".join((r.title or "").split())[:72]
        print(f"    [{day}] {r.name[:18]:<18} {title}")
    if len(rows) > cap:
        print(f"    … and {len(rows) - cap} more")


async def _sample_ids(db, having: str) -> list[int]:
    return (
        (
            await db.execute(
                text(
                    "select cluster_id from article_cluster group by cluster_id "
                    f"having {having} order by random() limit :n"
                ),
                {"n": _N},
            )
        )
        .scalars()
        .all()
    )


async def multi_source(db) -> None:
    _hr("RANDOM MULTI-SOURCE CLUSTERS (each should be ONE story)")
    for cid in await _sample_ids(db, "count(*) between 3 and 8"):
        rows = await _members(db, cid)
        print(f"\n  cluster #{cid}  ({len(rows)} sources):")
        _print_members(rows)


async def largest(db) -> None:
    _hr("LARGEST CLUSTERS (coherent, or chained mega-blobs?)")
    ids = (
        (
            await db.execute(
                text(
                    "select cluster_id from article_cluster group by cluster_id "
                    "order by count(*) desc limit :n"
                ),
                {"n": _N},
            )
        )
        .scalars()
        .all()
    )
    for cid in ids:
        rows = await _members(db, cid)
        print(f"\n  cluster #{cid}  ({len(rows)} sources):")
        _print_members(rows, cap=8)


async def singletons(db) -> None:
    _hr("RANDOM SINGLETONS (genuinely unique stories, or missed matches?)")
    for cid in await _sample_ids(db, "count(*) = 1"):
        rows = await _members(db, cid)
        r = rows[0]
        day = r.published_at.strftime("%Y-%m-%d") if r.published_at else "----------"
        title = " ".join((r.title or "").split())[:72]
        print(f"  #{cid} [{day}] {r.name[:18]:<18} {title}")


async def main() -> None:
    async with SessionLocal() as db:
        await multi_source(db)
        await largest(db)
        await singletons(db)
        print("\nDone.\n")


if __name__ == "__main__":
    asyncio.run(main())
