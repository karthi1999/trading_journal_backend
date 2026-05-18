from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.crud import account as crud_account
from app.db import get_db
from app.models import AccountType
from app.schemas.account import AccountCreate, AccountResponse

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountResponse])
async def list_accounts(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AccountResponse]:
    items = await crud_account.list_for_user(db, user.id)
    return [AccountResponse.from_model(a) for a in items]


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    payload: AccountCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AccountResponse:
    a = await crud_account.create(
        db,
        user_id=user.id,
        name=payload.name,
        broker_name=payload.broker_name,
        account_number=payload.account_number,
        type=AccountType(payload.type),
        balance=payload.balance,
        currency=payload.currency,
    )
    return AccountResponse.from_model(a)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    a = await crud_account.get(db, account_id)
    if not a or a.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    await crud_account.delete(db, a)
