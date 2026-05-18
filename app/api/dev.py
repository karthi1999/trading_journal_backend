from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.crud import expense as crud_expense
from app.crud import investment as crud_investment
from app.crud import trade as crud_trade
from app.db import get_db
from app.services import seed as seed_service

router = APIRouter(prefix="/dev", tags=["dev"])


@router.post("/seed-trades")
async def seed_trades(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365),
    count: int = Query(default=60, ge=1, le=500),
    seed: int = Query(default=42),
) -> dict:
    """Generate demo trades for the current user. Idempotent — wipes existing trades first."""
    return await seed_service.seed_trades(
        db, user_id=user.id, days=days, count=count, seed=seed
    )


@router.delete("/clear-trades")
async def clear_trades(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Wipe all trades for the current user."""
    deleted = await crud_trade.delete_all_for_user(db, user.id)
    return {"deleted": deleted}


@router.post("/seed-investments")
async def seed_investments(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Generate demo investments for the current user. Idempotent — wipes existing first."""
    return await seed_service.seed_investments(db, user_id=user.id)


@router.delete("/clear-investments")
async def clear_investments(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Wipe all investments for the current user."""
    deleted = await crud_investment.delete_all_for_user(db, user.id)
    return {"deleted": deleted}


@router.post("/seed-expenses")
async def seed_expenses(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Generate demo expenses for the current user. Idempotent — wipes existing first."""
    return await seed_service.seed_expenses(db, user_id=user.id)


@router.delete("/clear-expenses")
async def clear_expenses(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Wipe all expenses for the current user."""
    deleted = await crud_expense.delete_all_for_user(db, user.id)
    return {"deleted": deleted}
