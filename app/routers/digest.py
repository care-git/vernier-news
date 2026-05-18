from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/digest", tags=["digest"])


@router.get("/")
async def get_digest(_: User = Depends(get_current_user)) -> dict:
    # Phase 2 deliverable — digest generation not yet implemented
    return {"items": []}
