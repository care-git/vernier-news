from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.cache.digest import get_digest
from app.models.user import User
from app.schemas.digest import DigestResponse

router = APIRouter(prefix="/digest", tags=["digest"])


@router.get("/", response_model=DigestResponse)
async def get_digest_endpoint(current_user: User = Depends(get_current_user)) -> dict:
    cached = await get_digest(current_user.id)
    if cached is not None:
        return cached
    return {"user_id": current_user.id, "generated_at": "", "categories": {}}
