"""require a minimum absolute count of shared entities to corroborate a cluster join

Revision ID: 0014
Revises: 0013
Create Date: 2026-08-01

The mid-band join rule accepted an entity overlap *coefficient* of 0.30, which divides
by the smaller of the two entity sets — almost always the incoming article's. A
three-entity article sharing one name scored 0.33 and joined.

Because a cluster's entity cache accumulates every entity it has ever seen, the chance
of sharing at least one name rises with cluster size, so large clusters became
attractors: the more they held, the more they pulled in. That is the mechanism behind
the six 300-to-564-article clusters, where a quarter of same-cluster pairs sit below
the minimum join threshold and are connected only through intermediaries.

Requiring two shared entities is a strict tightening — it can only remove joins that
previously happened on a single shared name, never add new ones — which keeps its
effect bounded and measurable against the 29 July baseline (same-cluster p25 = 0.681,
11+ bucket holding 9,756 articles).
"""

from alembic import op

revision: str = "0014"
down_revision: str = "0013"
branch_labels = None
depends_on = None

_KEY = "join_entity_min_shared"
_VALUE = 2.0
_DESCRIPTION = "Minimum shared entities required for an entity-corroborated join"


def upgrade() -> None:
    op.execute(
        "INSERT INTO settings (key, value, category, description) "
        f"VALUES ('{_KEY}', {_VALUE}, 'clustering', '{_DESCRIPTION}') "
        f"ON CONFLICT (key) DO UPDATE SET value = {_VALUE}"
    )


def downgrade() -> None:
    op.execute(f"DELETE FROM settings WHERE key = '{_KEY}'")
