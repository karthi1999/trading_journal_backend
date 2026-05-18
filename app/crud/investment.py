from typing import Any

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Investment, InvestmentType


async def list_for_user(db: AsyncSession, user_id: str) -> list[Investment]:
    result = await db.execute(
        select(Investment)
        .where(Investment.user_id == user_id)
        .order_by(Investment.created_at.desc())
    )
    return list(result.scalars().all())


async def get(db: AsyncSession, investment_id: str) -> Investment | None:
    return await db.get(Investment, investment_id)


async def create(db: AsyncSession, *, user_id: str, fields: dict[str, Any]) -> Investment:
    fields = dict(fields)
    if "type" in fields and not isinstance(fields["type"], InvestmentType):
        fields["type"] = InvestmentType(fields["type"])
    investment = Investment(user_id=user_id, **fields)
    db.add(investment)
    await db.commit()
    await db.refresh(investment)
    return investment


async def update(
    db: AsyncSession, investment: Investment, fields: dict[str, Any]
) -> Investment:
    if "type" in fields and fields["type"] is not None and not isinstance(
        fields["type"], InvestmentType
    ):
        fields["type"] = InvestmentType(fields["type"])
    for k, v in fields.items():
        setattr(investment, k, v)
    await db.commit()
    await db.refresh(investment)
    return investment


async def delete(db: AsyncSession, investment: Investment) -> None:
    await db.delete(investment)
    await db.commit()


async def delete_all_for_user(db: AsyncSession, user_id: str) -> int:
    result = await db.execute(sa_delete(Investment).where(Investment.user_id == user_id))
    await db.commit()
    return result.rowcount or 0
