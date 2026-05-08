from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user
from app.db import prisma
from app.schemas.account import AccountCreate, AccountResponse

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountResponse])
async def list_accounts(user=Depends(get_current_user)) -> list[AccountResponse]:
    items = await prisma.account.find_many(where={"userId": user.id}, order={"createdAt": "asc"})
    return [AccountResponse.from_model(a) for a in items]


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(payload: AccountCreate, user=Depends(get_current_user)) -> AccountResponse:
    a = await prisma.account.create(
        data={
            "userId": user.id,
            "name": payload.name,
            "brokerName": payload.broker_name,
            "accountNumber": payload.account_number,
            "type": payload.type,
            "balance": payload.balance,
            "currency": payload.currency,
        }
    )
    return AccountResponse.from_model(a)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(account_id: str, user=Depends(get_current_user)) -> None:
    a = await prisma.account.find_unique(where={"id": account_id})
    if not a or a.userId != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    await prisma.account.delete(where={"id": account_id})
