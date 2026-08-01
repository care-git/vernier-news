"""record wire tier 4 explicitly so NULL can mean "not yet computed"

Revision ID: 0013
Revises: 0012
Create Date: 2026-07-29

Wire tier is derived from vector similarity, so an article ingested without an
embedding cannot have one. Deferred embedding therefore introduces a second reason
for wire_tier to be NULL, and the column previously used NULL for tier 4 as well —
leaving "checked, and it is original reporting" indistinguishable from "never
checked". Across a multi-million-row historical ingest that ambiguity is permanent.

Tier 4 is now stored as 4. Every existing article has been through get_wire_tier, so
every existing NULL is a tier 4 and converts safely.

No behaviour changes: the tier-to-independence mapping in app/pipeline/clustering.py
already scores tier 4 and NULL identically at 1.0.
"""

from alembic import op

revision: str = "0013"
down_revision: str = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE articles SET wire_tier = 4 WHERE wire_tier IS NULL")


def downgrade() -> None:
    op.execute("UPDATE articles SET wire_tier = NULL WHERE wire_tier = 4")
