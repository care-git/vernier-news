from pydantic import BaseModel

from app.schemas.cluster import ClusterSummary


class DigestResponse(BaseModel):
    user_id: int
    generated_at: str
    categories: dict[str, list[ClusterSummary]]
