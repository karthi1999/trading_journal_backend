from datetime import date as date_
from typing import Any

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Expense, ExpenseCategory


async def list_for_user(
    db: AsyncSession,
    *,
    user_id: str,
    start: date_ | None = None,
    end: date_ | None = None,
    category: ExpenseCategory | None = None,
    limit: int = 500,
) -> list[Expense]:
    stmt = select(Expense).where(Expense.user_id == user_id)
    if start:
        stmt = stmt.where(Expense.expense_date >= start)
    if end:
        stmt = stmt.where(Expense.expense_date <= end)
    if category:
        stmt = stmt.where(Expense.category == category)
    stmt = stmt.order_by(Expense.expense_date.desc(), Expense.created_at.desc()).limit(
        limit
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get(db: AsyncSession, expense_id: str) -> Expense | None:
    return await db.get(Expense, expense_id)


async def create(db: AsyncSession, *, user_id: str, fields: dict[str, Any]) -> Expense:
    data = dict(fields)
    if "category" in data and not isinstance(data["category"], ExpenseCategory):
        data["category"] = ExpenseCategory(data["category"])
    expense = Expense(user_id=user_id, **data)
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    return expense


async def update(db: AsyncSession, expense: Expense, fields: dict[str, Any]) -> Expense:
    if "category" in fields and fields["category"] is not None and not isinstance(
        fields["category"], ExpenseCategory
    ):
        fields["category"] = ExpenseCategory(fields["category"])
    for k, v in fields.items():
        setattr(expense, k, v)
    await db.commit()
    await db.refresh(expense)
    return expense


async def delete(db: AsyncSession, expense: Expense) -> None:
    await db.delete(expense)
    await db.commit()


async def delete_all_for_user(db: AsyncSession, user_id: str) -> int:
    result = await db.execute(sa_delete(Expense).where(Expense.user_id == user_id))
    await db.commit()
    return result.rowcount or 0
