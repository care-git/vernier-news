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


class ClusterSourceOutlet(BaseModel):
    """Outlet fields shown on a source row and its inline card."""

    id: int
    name: str
    domain: str
    country: str | None = None
    political_leaning_lr: float | None = None
    parent_org_name: str | None = None


class ClusterSource(BaseModel):
    """A single member article of a cluster, with its outlet context."""

    article_id: int
    title: str
    url: str
    published_at: str | None = None
    author: str | None = None
    wire_tier: int | None = None
    independence_score: float
    outlet: ClusterSourceOutlet


class CountryCount(BaseModel):
    country: str
    count: int


class ClusterDetail(ClusterSummary):
    """Full cluster view: summary fields plus the member source list."""

    sources: list[ClusterSource] = []
    country_counts: list[CountryCount] = []
