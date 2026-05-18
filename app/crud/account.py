from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Account, AccountType


async def list_for_user(db: AsyncSession, user_id: str) -> list[Account]:
    result = await db.execute(
        select(Account).where(Account.user_id == user_id).order_by(Account.created_at.asc())
    )
    return list(result.scalars().all())


async def get(db: AsyncSession, account_id: str) -> Account | None:
    return await db.get(Account, account_id)


async def create(
    db: AsyncSession,
    *,
    user_id: str,
    name: str,
    broker_name: str | None,
    account_number: str | None,
    type: AccountType,
    balance: Decimal,
    currency: str,
) -> Account:
    account = Account(
        user_id=user_id,
        name=name,
        broker_name=broker_name,
        account_number=account_number,
        type=type,
        balance=balance,
        currency=currency,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def delete(db: AsyncSession, account: Account) -> None:
    await db.delete(account)
    await db.commit()
