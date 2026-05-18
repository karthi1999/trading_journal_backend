from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Strategy


async def list_for_user(db: AsyncSession, user_id: str) -> list[Strategy]:
    result = await db.execute(
        select(Strategy)
        .where(Strategy.user_id == user_id)
        .order_by(Strategy.created_at.desc())
    )
    return list(result.scalars().all())


async def get(db: AsyncSession, strategy_id: str) -> Strategy | None:
    return await db.get(Strategy, strategy_id)


async def create(
    db: AsyncSession,
    *,
    user_id: str,
    name: str,
    description: str | None,
    entry_criteria: list[Any],
    exit_criteria: list[Any],
) -> Strategy:
    strategy = Strategy(
        user_id=user_id,
        name=name,
        description=description,
        entry_criteria=entry_criteria,
        exit_criteria=exit_criteria,
    )
    db.add(strategy)
    await db.commit()
    await db.refresh(strategy)
    return strategy


async def update(db: AsyncSession, strategy: Strategy, fields: dict[str, Any]) -> Strategy:
    for k, v in fields.items():
        setattr(strategy, k, v)
    await db.commit()
    await db.refresh(strategy)
    return strategy


async def delete(db: AsyncSession, strategy: Strategy) -> None:
    await db.delete(strategy)
    await db.commit()
