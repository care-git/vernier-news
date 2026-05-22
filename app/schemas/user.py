from pydantic import BaseModel


class UserPreferencesRequest(BaseModel):
    purpose: str = "general"  # general | journalist | researcher | analyst
    interests: list[str] = []  # category slugs
    depth_preference: str = "standard"  # brief | standard | deep


class UserPreferencesResponse(BaseModel):
    purpose: str
    interests: list[str]
    depth_preference: str
