from datetime import date as date_
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Investment, InvestmentTransaction, TransactionType


async def list_for_investment(
    db: AsyncSession, investment_id: str
) -> list[InvestmentTransaction]:
    result = await db.execute(
        select(InvestmentTransaction)
        .where(InvestmentTransaction.investment_id == investment_id)
        .order_by(
            InvestmentTransaction.transaction_date.desc(),
            InvestmentTransaction.created_at.desc(),
        )
    )
    return list(result.scalars().all())


async def list_for_user(
    db: AsyncSession,
    *,
    user_id: str,
    start: date_ | None = None,
    end: date_ | None = None,
) -> list[InvestmentTransaction]:
    stmt = (
        select(InvestmentTransaction)
        .where(InvestmentTransaction.user_id == user_id)
        .options(selectinload(InvestmentTransaction.investment))
    )
    if start:
        stmt = stmt.where(InvestmentTransaction.transaction_date >= start)
    if end:
        stmt = stmt.where(InvestmentTransaction.transaction_date <= end)
    stmt = stmt.order_by(InvestmentTransaction.transaction_date.asc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get(
    db: AsyncSession, transaction_id: str
) -> InvestmentTransaction | None:
    return await db.get(InvestmentTransaction, transaction_id)


async def create(
    db: AsyncSession,
    *,
    user_id: str,
    investment: Investment,
    tx_type: TransactionType,
    quantity: Decimal,
    price: Decimal,
    fees: Decimal,
    transaction_date: date_,
    notes: str | None,
) -> InvestmentTransaction:
    tx = InvestmentTransaction(
        user_id=user_id,
        investment_id=investment.id,
        type=tx_type,
        quantity=quantity,
        price=price,
        fees=fees,
        transaction_date=transaction_date,
        notes=notes,
    )
    db.add(tx)
    await db.commit()
    await db.refresh(tx)
    return tx


async def delete(db: AsyncSession, tx: InvestmentTransaction) -> None:
    await db.delete(tx)
    await db.commit()
