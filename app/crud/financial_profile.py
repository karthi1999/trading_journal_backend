from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FinancialProfile


async def get_for_user(db: AsyncSession, user_id: str) -> FinancialProfile | None:
    result = await db.execute(
        select(FinancialProfile).where(FinancialProfile.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def upsert(
    db: AsyncSession,
    *,
    user_id: str,
    age: int | None,
    monthly_income: Decimal | None,
    monthly_family_expense: Decimal | None,
    monthly_savings: Decimal | None,
    currency: str,
    usd_inr_rate: Decimal | None,
) -> FinancialProfile:
    # INSERT side uses ORM attribute names (SQLAlchemy maps to DB columns).
    values = {
        "user_id": user_id,
        "age": age,
        "monthly_income": monthly_income,
        "monthly_family_expense": monthly_family_expense,
        "monthly_savings": monthly_savings,
        "currency": currency,
        "usd_inr_rate": usd_inr_rate,
    }
    # ON CONFLICT ... SET takes raw column names — must match the actual DB columns
    # (camelCase, since Prisma created them without `@map`).
    set_values = {
        "age": age,
        "monthlyIncome": monthly_income,
        "monthlyFamilyExpense": monthly_family_expense,
        "monthlySavings": monthly_savings,
        "currency": currency,
        "usdInrRate": usd_inr_rate,
    }
    stmt = (
        insert(FinancialProfile)
        .values(**values)
        .on_conflict_do_update(index_elements=[FinancialProfile.user_id], set_=set_values)
        .returning(FinancialProfile)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one()
