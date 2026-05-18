from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db import get_db
from app.schemas.analytics import DashboardSummary
from app.services import analytics as analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardSummary)
async def dashboard(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    account_id: str | None = Query(default=None),
    verified: bool | None = Query(default=None),
    month: str | None = Query(
        default=None, description="YYYY-MM. When set, overrides start/end to that calendar month."
    ),
) -> DashboardSummary:
    return await analytics_service.compute_dashboard(
        db,
        user_id=user.id,
        start=start,
        end=end,
        account_id=account_id,
        verified=verified,
        month=month,
    )
