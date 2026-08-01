from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EntityMention(Base):
    """One named entity as it appeared in one article.

    spaCy already runs NER on every article at ingest; until now the output was
    collapsed into a cluster's entity_cache and the per-article detail thrown away.
    Persisting it costs a table and no extra compute, while recovering it later would
    mean re-running NER over the whole corpus — the capture-now/render-later principle
    in docs/data-model.md.

    Deliberately unresolved. There is no entity_id yet: linking surface forms to
    canonical Wikidata identities is Phase 4 (CONCEPT.md §10), and inventing an
    entities table before the resolution method exists would fix the wrong shape.
    ``normalised`` is the cheap interim grouping key — lowercased, honorifics stripped
    — which is what clustering already compares on.
    """

    __tablename__ = "entity_mentions"

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), nullable=False, index=True)
    # As written in the article: "President Trump", "the Fed Chair".
    surface_form: Mapped[str] = mapped_column(Text, nullable=False)
    # Lowercased and de-titled, so surface variants group without resolution.
    normalised: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    # spaCy label: PERSON, ORG, GPE, LOC, EVENT, NORP.
    label: Mapped[str] = mapped_column(String(16), nullable=False)
    # Character offset into title + body, for later provenance and quotation.
    start_char: Mapped[int] = mapped_column(Integer, nullable=False)

    article: Mapped["Article"] = relationship(back_populates="mentions")  # noqa: F821
