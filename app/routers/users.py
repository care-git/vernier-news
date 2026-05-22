from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User, UserPreferences
from app.schemas.user import UserPreferencesRequest, UserPreferencesResponse

router = APIRouter(prefix="/users", tags=["users"])


class UserResponse(BaseModel):
    id: int
    email: str
    tier: str


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(id=current_user.id, email=current_user.email, tier=current_user.tier)


@router.put("/preferences", response_model=UserPreferencesResponse)
async def update_preferences(
    body: UserPreferencesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserPreferencesResponse:
    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()
    if prefs is None:
        prefs = UserPreferences(user_id=current_user.id)
        db.add(prefs)

    prefs.categories = {"purpose": body.purpose, "interests": body.interests}
    prefs.depth_preference = body.depth_preference
    await db.commit()
    await db.refresh(prefs)

    cats = prefs.categories or {}
    return UserPreferencesResponse(
        purpose=cats.get("purpose", "general"),
        interests=cats.get("interests", []),
        depth_preference=prefs.depth_preference or "standard",
    )
