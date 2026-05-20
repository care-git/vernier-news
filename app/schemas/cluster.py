from pydantic import BaseModel


class PoliticalSpread(BaseModel):
    mean: float
    min: float
    max: float


class ClusterSummary(BaseModel):
    id: int
    headline: str
    total_source_count: int
    independent_source_count: int
    category: str | None = None
    first_published_at: str | None = None
    last_updated_at: str
    political_spread: PoliticalSpread | None = None
    countries: list[str] = []
