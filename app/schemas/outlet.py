from pydantic import BaseModel


class OutletSummary(BaseModel):
    id: int
    name: str
    domain: str
    country: str | None = None
    political_leaning_lr: float | None = None


class OutletDetail(OutletSummary):
    language_primary: str | None = None
    political_leaning_source: str | None = None
    parent_org_name: str | None = None
    active: bool
