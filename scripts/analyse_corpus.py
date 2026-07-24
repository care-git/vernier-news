"""Read-only audit of the corpus: composition, source health, cluster shape, and the
bge-m3 similarity distributions needed to calibrate clustering.

    make analyse
    # equivalently: docker compose exec api python -m scripts.analyse_corpus

Safe to run against production — it only reads, and every expensive step is sampled.
Embeddings are L2-normalised, so cosine similarity is just a dot product; the
pairwise sections compute that client-side with numpy.
"""

from __future__ import annotations

import asyncio

import numpy as np
from sqlalchemy import func, select, text

from app.database import SessionLocal
from app.models.article import Article
from app.models.cluster import ArticleCluster, Cluster
from app.models.outlet import Outlet

_PAIR_SAMPLE = 500  # articles pulled into memory for the random-pair baseline
_CLUSTER_SAMPLE = 100  # multi-member clusters sampled for intra-cluster similarity
_KNN_SAMPLE = 200  # articles probed against the full corpus via the index
_THRESHOLDS = (0.95, 0.90, 0.85, 0.80, 0.75, 0.70, 0.65)


def section(title: str) -> None:
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")


def describe(label: str, values) -> None:
    a = np.asarray(values, dtype=float)
    if a.size == 0:
        print(f"{label:<26} (no data)")
        return
    p = np.percentile(a, [5, 25, 50, 75, 95])
    print(
        f"{label:<26} n={a.size:<7,} mean={a.mean():.3f}  "
        f"p5={p[0]:.3f} p25={p[1]:.3f} p50={p[2]:.3f} p75={p[3]:.3f} p95={p[4]:.3f}"
    )


async def overview(db) -> int:
    section("1. CORPUS OVERVIEW")
    articles = await db.scalar(select(func.count()).select_from(Article)) or 0
    clusters = await db.scalar(select(func.count()).select_from(Cluster)) or 0
    active = await db.scalar(
        select(func.count()).select_from(Cluster).where(Cluster.active.is_(True))
    )
    memberships = await db.scalar(select(func.count()).select_from(ArticleCluster)) or 0
    outlets = await db.scalar(select(func.count()).select_from(Outlet))
    no_body = await db.scalar(
        select(func.count()).select_from(Article).where(Article.body.is_(None))
    )
    short_body = await db.scalar(
        select(func.count()).select_from(Article).where(func.length(Article.body) < 200)
    )
    no_pub = await db.scalar(
        select(func.count()).select_from(Article).where(Article.published_at.is_(None))
    )
    no_emb = await db.scalar(
        select(func.count()).select_from(Article).where(Article.embedding.is_(None))
    )
    uncat = await db.scalar(
        select(func.count()).select_from(Article).where(Article.category_id.is_(None))
    )
    lo, hi = (
        await db.execute(select(func.min(Article.published_at), func.max(Article.published_at)))
    ).one()

    share = lambda n: f"{n / articles:.1%}" if articles else "n/a"  # noqa: E731
    print(f"articles              : {articles:,}")
    print(f"clusters              : {clusters:,}   (active {active:,})")
    print(f"memberships           : {memberships:,}")
    if clusters:
        print(f"articles per cluster  : {memberships / clusters:.2f}")
    print(f"outlets               : {outlets}")
    print(f"published range       : {lo} -> {hi}")
    print(f"no body               : {no_body:,} ({share(no_body)})")
    print(f"body < 200 chars      : {short_body:,}  (embedding is title-dominated)")
    print(f"no published_at       : {no_pub:,}  (breaks temporal windows)")
    print(f"no embedding          : {no_emb:,}")
    print(f"uncategorised         : {uncat:,} ({share(uncat)})")
    return articles


async def ingestion_rate(db) -> None:
    section("2. INGESTION OVER THE LAST 14 DAYS")
    rows = (
        await db.execute(
            text(
                "select date(collected_at) as day, count(*) as n from articles "
                "where collected_at >= now() - interval '14 days' group by 1 order by 1"
            )
        )
    ).all()
    if not rows:
        print("(no articles collected in the last 14 days — ingestion may be stalled)")
        return
    peak = max(r.n for r in rows)
    for r in rows:
        bar = "#" * max(1, round(40 * r.n / peak))
        print(f"  {r.day}  {r.n:>6,}  {bar}")


async def sources(db) -> None:
    section("3. SOURCE COMPOSITION AND HEALTH")
    rows = (
        await db.execute(
            text(
                "select o.name, o.country, o.active, count(a.id) as n, max(a.collected_at) as last_seen "
                "from outlets o left join articles a on a.outlet_id = o.id "
                "group by o.id, o.name, o.country, o.active order by n desc"
            )
        )
    ).all()
    total = sum(r.n for r in rows) or 1
    print(f"{'outlet':<28}{'country':<9}{'articles':>10}{'share':>8}   last seen")
    for r in rows:
        flag = "" if r.active else "  [inactive]"
        print(
            f"{r.name[:27]:<28}{(r.country or '-'):<9}{r.n:>10,}{r.n / total:>7.1%}   {r.last_seen}{flag}"
        )

    silent = [r.name for r in rows if r.n == 0]
    if silent:
        print(f"\noutlets that have never produced an article: {', '.join(silent)}")

    section("3b. LANGUAGE DISTRIBUTION")
    langs = (
        await db.execute(
            text(
                "select coalesce(language,'unknown') as lang, count(*) as n from articles "
                "group by 1 order by n desc limit 15"
            )
        )
    ).all()
    for r in langs:
        print(f"  {r.lang:<10}{r.n:>8,}  ({r.n / total:.1%})")
    print("\n(bge-m3 is multilingual — if this is ~all English, that capability is unused for now)")


async def leaning(db) -> None:
    section("4. POLITICAL LEANING COVERAGE")
    rows = (
        await db.execute(
            text(
                "select o.name, o.political_leaning_lr as lean, count(a.id) as n "
                "from outlets o left join articles a on a.outlet_id = o.id "
                "group by o.id, o.name, o.political_leaning_lr order by lean nulls last"
            )
        )
    ).all()
    missing = [r.name for r in rows if r.lean is None]
    print(f"outlets with leaning  : {sum(1 for r in rows if r.lean is not None)} / {len(rows)}")
    if missing:
        print(f"missing leaning       : {', '.join(missing)}")

    buckets = {
        "left (<=-0.6)": 0,
        "centre-left": 0,
        "centre": 0,
        "centre-right": 0,
        "right (>=0.6)": 0,
    }
    for r in rows:
        if r.lean is None:
            continue
        if r.lean <= -0.6:
            buckets["left (<=-0.6)"] += r.n
        elif r.lean <= -0.2:
            buckets["centre-left"] += r.n
        elif r.lean < 0.2:
            buckets["centre"] += r.n
        elif r.lean < 0.6:
            buckets["centre-right"] += r.n
        else:
            buckets["right (>=0.6)"] += r.n
    weighted = sum(buckets.values()) or 1
    print("\narticle-weighted spectrum coverage (agnosticism check):")
    for name, n in buckets.items():
        bar = "#" * round(40 * n / weighted)
        print(f"  {name:<16}{n:>8,}  {n / weighted:>6.1%}  {bar}")


async def wire_tiers(db) -> None:
    section("5. WIRE TIER DETECTION")
    rows = (
        await db.execute(
            text(
                "select coalesce(wire_tier::text,'none (tier 4 / original)') as tier, count(*) as n "
                "from articles group by 1 order by 1"
            )
        )
    ).all()
    for r in rows:
        print(f"  tier {r.tier:<28}{r.n:>8,}")


async def cluster_shape(db) -> None:
    section("6. CLUSTER SIZE DISTRIBUTION")
    rows = (
        await db.execute(
            text(
                "select case when size = 1 then '1 (singleton)' when size = 2 then '2' "
                "when size = 3 then '3' when size between 4 and 5 then '4-5' "
                "when size between 6 and 10 then '6-10' else '11+' end as bucket, "
                "count(*) as clusters, sum(size) as articles from ("
                "  select cluster_id, count(*) as size from article_cluster group by 1"
                ") t group by 1 order by min(size)"
            )
        )
    ).all()
    total_clusters = sum(r.clusters for r in rows) or 1
    print(f"{'size':<16}{'clusters':>10}{'share':>8}{'articles':>11}")
    for r in rows:
        print(
            f"{r.bucket:<16}{r.clusters:>10,}{r.clusters / total_clusters:>7.1%}{r.articles:>11,}"
        )


async def similarity_profile(db) -> None:
    section("7. SIMILARITY DISTRIBUTIONS (bge-m3)")

    # 7a — random-pair baseline
    rows = (
        await db.execute(
            select(Article.embedding)
            .where(Article.embedding.isnot(None))
            .order_by(func.random())
            .limit(_PAIR_SAMPLE)
        )
    ).all()
    if len(rows) < 2:
        print("not enough embedded articles to profile")
        return
    vecs = np.asarray([r[0] for r in rows], dtype=np.float32)
    sims = vecs @ vecs.T
    iu = np.triu_indices(len(vecs), k=1)
    describe("random pairs", sims[iu])

    # 7b — intra-cluster similarity, only from clusters that actually grouped
    cluster_ids = (
        (
            await db.execute(
                text(
                    "select cluster_id from article_cluster group by cluster_id "
                    "having count(*) >= 2 order by random() limit :n"
                ),
                {"n": _CLUSTER_SAMPLE},
            )
        )
        .scalars()
        .all()
    )
    intra: list[float] = []
    for cid in cluster_ids:
        members = (
            await db.execute(
                select(Article.embedding)
                .join(ArticleCluster, ArticleCluster.article_id == Article.id)
                .where(ArticleCluster.cluster_id == cid)
                .where(Article.embedding.isnot(None))
            )
        ).all()
        if len(members) < 2:
            continue
        m = np.asarray([r[0] for r in members], dtype=np.float32)
        s = m @ m.T
        iu2 = np.triu_indices(len(m), k=1)
        intra.extend(s[iu2].tolist())
    describe("same-cluster pairs", intra)

    # 7c — nearest neighbour across the whole corpus (this sets the join threshold)
    probes = (
        await db.execute(
            select(Article.id, Article.embedding, ArticleCluster.cluster_id)
            .join(ArticleCluster, ArticleCluster.article_id == Article.id)
            .where(Article.embedding.isnot(None))
            .order_by(func.random())
            .limit(_KNN_SAMPLE)
        )
    ).all()

    top1: list[float] = []
    cross_cluster: list[tuple[float, bool]] = []
    for aid, emb, own_cluster in probes:
        neighbours = (
            await db.execute(
                select(
                    ArticleCluster.cluster_id,
                    Article.embedding.cosine_distance(emb).label("d"),
                )
                .join(ArticleCluster, ArticleCluster.article_id == Article.id)
                .where(Article.id != aid)
                .where(Article.embedding.isnot(None))
                .order_by(Article.embedding.cosine_distance(emb))
                .limit(1)
            )
        ).all()
        if not neighbours:
            continue
        sim = 1.0 - neighbours[0].d
        top1.append(sim)
        cross_cluster.append((sim, neighbours[0].cluster_id != own_cluster))
    describe("nearest neighbour", top1)

    section("8. CONSOLIDATION OPPORTUNITY")
    print("Of the sampled articles, how many have their nearest neighbour sitting in a")
    print("DIFFERENT cluster? Those are pairs the current rule failed to group.\n")
    print(f"{'similarity >=':<16}{'articles':>10}{'share of sample':>18}")
    n = len(cross_cluster) or 1
    for t in _THRESHOLDS:
        hits = sum(1 for sim, different in cross_cluster if sim >= t and different)
        print(f"{t:<16.2f}{hits:>10,}{hits / n:>17.1%}")
    print("\nThis is the single most useful number for picking the join threshold and the")
    print("consolidation merge distance: it estimates how much regrouping is available.")


async def index_health(db) -> None:
    section("9. INDEX HEALTH")
    rows = (
        (await db.execute(text("select indexname from pg_indexes where tablename = 'articles'")))
        .scalars()
        .all()
    )
    print("indexes on articles:", ", ".join(rows) or "(none)")

    sample = await db.scalar(
        select(Article.embedding).where(Article.embedding.isnot(None)).limit(1)
    )
    if sample is None:
        return
    literal = "[" + ",".join(f"{x:.6f}" for x in sample) + "]"
    plan = (
        (
            await db.execute(
                text(
                    "explain select id from articles where embedding is not null "
                    f"order by embedding <=> '{literal}'::vector limit 5"
                )
            )
        )
        .scalars()
        .all()
    )
    print("\nKNN query plan:")
    for line in plan:
        print("  " + line)
    used = any("Index Scan" in line for line in plan)
    print(f"\n=> HNSW index {'IS' if used else 'is NOT'} being used for nearest-neighbour search")


async def main() -> None:
    async with SessionLocal() as db:
        articles = await overview(db)
        if not articles:
            print("\nempty corpus — nothing to analyse")
            return
        await ingestion_rate(db)
        await sources(db)
        await leaning(db)
        await wire_tiers(db)
        await cluster_shape(db)
        await similarity_profile(db)
        await index_health(db)
        print("\nDone.\n")


if __name__ == "__main__":
    asyncio.run(main())
