from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.crud import financial_profile as crud_profile
from app.db import get_db
from app.schemas.financial_profile import FinancialProfileResponse, FinancialProfileUpsert

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=FinancialProfileResponse | None)
async def get_profile(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FinancialProfileResponse | None:
    profile = await crud_profile.get_for_user(db, user.id)
    return FinancialProfileResponse.from_model(profile) if profile else None


@router.put("", response_model=FinancialProfileResponse)
async def upsert_profile(
    payload: FinancialProfileUpsert,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FinancialProfileResponse:
    profile = await crud_profile.upsert(
        db,
        user_id=user.id,
        age=payload.age,
        monthly_income=payload.monthly_income,
        monthly_family_expense=payload.monthly_family_expense,
        monthly_savings=payload.monthly_savings,
        currency=payload.currency,
        usd_inr_rate=payload.usd_inr_rate,
    )
    return FinancialProfileResponse.from_model(profile)
