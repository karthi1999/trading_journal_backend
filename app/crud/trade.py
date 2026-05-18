from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import MarketType, Trade, TradeSide, TradeStatus


async def list_for_user(
    db: AsyncSession,
    *,
    user_id: str,
    account_id: str | None = None,
    verified: bool | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 200,
    offset: int = 0,
    order_by: str = "openedAt_desc",
) -> list[Trade]:
    stmt = (
        select(Trade)
        .where(Trade.user_id == user_id)
        .options(selectinload(Trade.attachments))
    )
    if account_id:
        stmt = stmt.where(Trade.account_id == account_id)
    if verified is not None:
        stmt = stmt.where(Trade.is_verified == verified)
    if start:
        stmt = stmt.where(Trade.opened_at >= start)
    if end:
        stmt = stmt.where(Trade.opened_at <= end)

    if order_by == "closedAt_asc":
        stmt = stmt.order_by(Trade.closed_at.asc())
    else:
        stmt = stmt.order_by(Trade.opened_at.desc())

    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def list_closed_between(
    db: AsyncSession,
    *,
    user_id: str,
    start: datetime,
    end: datetime,
    account_id: str | None = None,
    verified: bool | None = None,
) -> list[Trade]:
    stmt = (
        select(Trade)
        .where(Trade.user_id == user_id)
        .where(Trade.closed_at.is_not(None))
        .where(Trade.closed_at >= start)
        .where(Trade.closed_at <= end)
        .options(selectinload(Trade.attachments))
    )
    if account_id:
        stmt = stmt.where(Trade.account_id == account_id)
    if verified is not None:
        stmt = stmt.where(Trade.is_verified == verified)
    stmt = stmt.order_by(Trade.closed_at.asc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get(db: AsyncSession, trade_id: str) -> Trade | None:
    result = await db.execute(
        select(Trade)
        .where(Trade.id == trade_id)
        .options(selectinload(Trade.attachments))
    )
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession,
    *,
    user_id: str,
    account_id: str,
    strategy_id: str | None,
    journal_id: str | None,
    symbol: str,
    side: TradeSide | str,
    status: TradeStatus | str,
    quantity: Decimal,
    entry_price: Decimal,
    exit_price: Decimal | None,
    pnl: Decimal,
    commission: Decimal,
    currency: str,
    market: MarketType | str,
    notes: str | None,
    tags: list[str],
    is_verified: bool,
    opened_at: datetime,
    closed_at: datetime | None,
) -> Trade:
    trade = Trade(
        user_id=user_id,
        account_id=account_id,
        strategy_id=strategy_id,
        journal_id=journal_id,
        symbol=symbol,
        side=side,
        status=status,
        quantity=quantity,
        entry_price=entry_price,
        exit_price=exit_price,
        pnl=pnl,
        commission=commission,
        currency=currency,
        market=market if isinstance(market, MarketType) else MarketType(market),
        notes=notes,
        tags=tags,
        is_verified=is_verified,
        opened_at=opened_at,
        closed_at=closed_at,
    )
    db.add(trade)
    await db.commit()
    await db.refresh(trade, attribute_names=["attachments"])
    return trade


async def update(db: AsyncSession, trade: Trade, fields: dict[str, Any]) -> Trade:
    for k, v in fields.items():
        setattr(trade, k, v)
    await db.commit()
    await db.refresh(trade, attribute_names=["attachments"])
    return trade


async def delete(db: AsyncSession, trade: Trade) -> None:
    await db.delete(trade)
    await db.commit()


async def delete_all_for_user(db: AsyncSession, user_id: str) -> int:
    result = await db.execute(sa_delete(Trade).where(Trade.user_id == user_id))
    await db.commit()
    return result.rowcount or 0
