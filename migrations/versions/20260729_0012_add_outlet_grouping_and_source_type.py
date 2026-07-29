"""add outlets.registrable_domain and outlets.source_type

Revision ID: 0012
Revises: 0011
Create Date: 2026-07-29

Two pieces of metadata that discovery-driven ingestion made necessary. The outlets
table went from 31 curated rows to over 1,600 in a day, and neither grouping nor kind
can be hand-maintained at that rate.

**registrable_domain** groups sibling sites discovered as separate outlets —
timesofindia.indiatimes.com with indiatimes.com, three iHeart stations under
iheart.com — using the public suffix list, since splitting on dots would reduce
bbc.co.uk to co.uk. It is a mechanical grouping, *not* ownership: aol.co.uk and
aol.com differ here and are the same company. Documented ownership is the influence
graph in Phase 4.

**source_type** records what kind of publisher a domain is. Discovery brought in
press-release wires, academic journals, government primary sources, NGOs, forums and
satire alongside journalism. Per "filter nothing, classify everything" none of it is
excluded — satire is a real part of the information landscape — but it must be
identifiable, both so users can filter graph views and so counting treats it
correctly: satire and press releases are coverage but not corroboration.

NULL means unclassified, which is the expected state for most outlets and never means
excluded. `wire_service` stays as it is: a wire service is a news organisation that
also syndicates, so the two are orthogonal and dedup keeps using the flag it has.
"""

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: str = "0011"
branch_labels = None
depends_on = None

_INDEX = "ix_outlets_registrable_domain"


def upgrade() -> None:
    op.add_column("outlets", sa.Column("registrable_domain", sa.String(255), nullable=True))
    op.add_column("outlets", sa.Column("source_type", sa.String(32), nullable=True))
    op.create_index(_INDEX, "outlets", ["registrable_domain"])


def downgrade() -> None:
    op.drop_index(_INDEX, table_name="outlets")
    op.drop_column("outlets", "source_type")
    op.drop_column("outlets", "registrable_domain")
