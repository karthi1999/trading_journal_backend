from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.crud import investment as crud_investment
from app.crud import investment_transaction as crud_tx
from app.db import get_db
from app.models import TransactionType
from app.schemas.investment import (
    InvestmentCreate,
    InvestmentResponse,
    InvestmentSummary,
    InvestmentUpdate,
)
from app.schemas.investment_transaction import (
    MonthlySummary,
    TransactionCreate,
    TransactionResponse,
)
from app.services import investments as investments_service

router = APIRouter(prefix="/investments", tags=["investments"])


@router.get("", response_model=list[InvestmentResponse])
async def list_investments(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[InvestmentResponse]:
    items = await crud_investment.list_for_user(db, user.id)
    return [InvestmentResponse.from_model(i) for i in items]


@router.get("/summary", response_model=InvestmentSummary)
async def summary(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InvestmentSummary:
    return await investments_service.compute_summary(db, user_id=user.id)


@router.post("", response_model=InvestmentResponse, status_code=status.HTTP_201_CREATED)
async def create_investment(
    payload: InvestmentCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InvestmentResponse:
    i = await crud_investment.create(
        db, user_id=user.id, fields=payload.model_dump()
    )
    return InvestmentResponse.from_model(i)


@router.patch("/{investment_id}", response_model=InvestmentResponse)
async def update_investment(
    investment_id: str,
    payload: InvestmentUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InvestmentResponse:
    existing = await crud_investment.get(db, investment_id)
    if not existing or existing.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Investment not found"
        )
    fields = payload.model_dump(exclude_unset=True)
    i = await crud_investment.update(db, existing, fields)
    return InvestmentResponse.from_model(i)


@router.delete("/{investment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_investment(
    investment_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    existing = await crud_investment.get(db, investment_id)
    if not existing or existing.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Investment not found"
        )
    await crud_investment.delete(db, existing)


@router.get("/monthly-summary", response_model=MonthlySummary)
async def monthly_summary(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    months: int = Query(default=12, ge=1, le=60),
) -> MonthlySummary:
    return await investments_service.compute_monthly_summary(
        db, user_id=user.id, months=months
    )


@router.get(
    "/{investment_id}/transactions", response_model=list[TransactionResponse]
)
async def list_transactions(
    investment_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TransactionResponse]:
    inv = await crud_investment.get(db, investment_id)
    if not inv or inv.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Investment not found"
        )
    items = await crud_tx.list_for_investment(db, investment_id)
    return [TransactionResponse.from_model(t) for t in items]


@router.post(
    "/{investment_id}/transactions",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_transaction(
    investment_id: str,
    payload: TransactionCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TransactionResponse:
    inv = await crud_investment.get(db, investment_id)
    if not inv or inv.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Investment not found"
        )

    tx_type = TransactionType(payload.type)
    if tx_type == TransactionType.BUY:
        investments_service.apply_buy(inv, payload.quantity, payload.price)
    else:
        investments_service.apply_sell(inv, payload.quantity)

    tx = await crud_tx.create(
        db,
        user_id=user.id,
        investment=inv,
        tx_type=tx_type,
        quantity=payload.quantity,
        price=payload.price,
        fees=payload.fees,
        transaction_date=payload.transaction_date,
        notes=payload.notes,
    )
    # `apply_*` mutated `inv` in place; the commit inside crud_tx.create persists both.
    return TransactionResponse.from_model(tx)


@router.delete(
    "/{investment_id}/transactions/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_transaction(
    investment_id: str,
    transaction_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    tx = await crud_tx.get(db, transaction_id)
    if not tx or tx.user_id != user.id or tx.investment_id != investment_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found"
        )
    await crud_tx.delete(db, tx)
    # NOTE: parent investment aggregates are not auto-reversed. Edit the
    # investment manually if you need to correct qty/avg cost after deletion.
