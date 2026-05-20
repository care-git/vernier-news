from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.outlet import Outlet
from app.schemas.outlet import OutletDetail, OutletSummary

router = APIRouter(prefix="/outlets", tags=["outlets"])


@router.get("/", response_model=list[OutletSummary])
async def list_outlets(db: AsyncSession = Depends(get_db)) -> list[dict]:
    result = await db.execute(select(Outlet).where(Outlet.active.is_(True)).limit(200))
    return [
        {
            "id": o.id,
            "name": o.name,
            "domain": o.domain,
            "country": o.country,
            "political_leaning_lr": o.political_leaning_lr,
        }
        for o in result.scalars()
    ]


@router.get("/{outlet_id}", response_model=OutletDetail)
async def get_outlet(outlet_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(Outlet).where(Outlet.id == outlet_id))
    outlet = result.scalar_one_or_none()
    if outlet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Outlet not found")
    return {
        "id": outlet.id,
        "name": outlet.name,
        "domain": outlet.domain,
        "country": outlet.country,
        "language_primary": outlet.language_primary,
        "political_leaning_lr": outlet.political_leaning_lr,
        "political_leaning_source": outlet.political_leaning_source,
        "parent_org_name": outlet.parent_org_name,
        "active": outlet.active,
    }
