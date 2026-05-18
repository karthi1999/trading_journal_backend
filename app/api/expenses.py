from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.crud import expense as crud_expense
from app.db import get_db
from app.models import ExpenseCategory
from app.schemas.expense import (
    ExpenseCreate,
    ExpenseResponse,
    ExpenseSummary,
    ExpenseUpdate,
)
from app.services import expenses as expenses_service

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.get("", response_model=list[ExpenseResponse])
async def list_expenses(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    category: str | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=2000),
) -> list[ExpenseResponse]:
    cat_enum: ExpenseCategory | None = None
    if category:
        try:
            cat_enum = ExpenseCategory(category)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category: {category}",
            ) from exc
    items = await crud_expense.list_for_user(
        db,
        user_id=user.id,
        start=start,
        end=end,
        category=cat_enum,
        limit=limit,
    )
    return [ExpenseResponse.from_model(e) for e in items]


@router.get("/summary", response_model=ExpenseSummary)
async def summary(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    months: int = Query(default=12, ge=1, le=60),
) -> ExpenseSummary:
    return await expenses_service.compute_summary(
        db, user_id=user.id, months=months
    )


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    payload: ExpenseCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExpenseResponse:
    e = await crud_expense.create(db, user_id=user.id, fields=payload.model_dump())
    return ExpenseResponse.from_model(e)


@router.patch("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: str,
    payload: ExpenseUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExpenseResponse:
    existing = await crud_expense.get(db, expense_id)
    if not existing or existing.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found"
        )
    fields = payload.model_dump(exclude_unset=True)
    e = await crud_expense.update(db, existing, fields)
    return ExpenseResponse.from_model(e)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    existing = await crud_expense.get(db, expense_id)
    if not existing or existing.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found"
        )
    await crud_expense.delete(db, existing)
