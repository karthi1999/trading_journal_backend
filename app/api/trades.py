from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_current_user
from app.db import prisma
from app.schemas.trade import TradeCreate, TradeResponse, TradeUpdate

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("", response_model=list[TradeResponse])
async def list_trades(
    user=Depends(get_current_user),
    account_id: str | None = None,
    verified: bool | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> list[TradeResponse]:
    where: dict = {"userId": user.id}
    if account_id:
        where["accountId"] = account_id
    if verified is not None:
        where["isVerified"] = verified
    if start or end:
        where["openedAt"] = {}
        if start:
            where["openedAt"]["gte"] = start
        if end:
            where["openedAt"]["lte"] = end

    items = await prisma.trade.find_many(
        where=where, order={"openedAt": "desc"}, take=limit, skip=offset
    )
    return [TradeResponse.from_model(t) for t in items]


@router.post("", response_model=TradeResponse, status_code=status.HTTP_201_CREATED)
async def create_trade(payload: TradeCreate, user=Depends(get_current_user)) -> TradeResponse:
    account = await prisma.account.find_unique(where={"id": payload.account_id})
    if not account or account.userId != user.id:
        raise HTTPException(status_code=400, detail="Invalid account")

    t = await prisma.trade.create(
        data={
            "userId": user.id,
            "accountId": payload.account_id,
            "strategyId": payload.strategy_id,
            "journalId": payload.journal_id,
            "symbol": payload.symbol.upper(),
            "side": payload.side,
            "status": payload.status,
            "quantity": payload.quantity,
            "entryPrice": payload.entry_price,
            "exitPrice": payload.exit_price,
            "pnl": payload.pnl,
            "commission": payload.commission,
            "notes": payload.notes,
            "tags": payload.tags,
            "isVerified": payload.is_verified,
            "openedAt": payload.opened_at,
            "closedAt": payload.closed_at,
        }
    )
    return TradeResponse.from_model(t)


@router.patch("/{trade_id}", response_model=TradeResponse)
async def update_trade(
    trade_id: str, payload: TradeUpdate, user=Depends(get_current_user)
) -> TradeResponse:
    existing = await prisma.trade.find_unique(where={"id": trade_id})
    if not existing or existing.userId != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade not found")

    field_map = {
        "strategy_id": "strategyId",
        "journal_id": "journalId",
        "symbol": "symbol",
        "side": "side",
        "status": "status",
        "quantity": "quantity",
        "entry_price": "entryPrice",
        "exit_price": "exitPrice",
        "pnl": "pnl",
        "commission": "commission",
        "notes": "notes",
        "tags": "tags",
        "is_verified": "isVerified",
        "opened_at": "openedAt",
        "closed_at": "closedAt",
    }
    data = {
        field_map[k]: v for k, v in payload.model_dump(exclude_unset=True).items() if k in field_map
    }
    if "symbol" in data and isinstance(data["symbol"], str):
        data["symbol"] = data["symbol"].upper()

    t = await prisma.trade.update(where={"id": trade_id}, data=data)
    return TradeResponse.from_model(t)


@router.delete("/{trade_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trade(trade_id: str, user=Depends(get_current_user)) -> None:
    existing = await prisma.trade.find_unique(where={"id": trade_id})
    if not existing or existing.userId != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade not found")
    await prisma.trade.delete(where={"id": trade_id})
