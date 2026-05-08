from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

TradeSide = Literal["LONG", "SHORT"]
TradeStatus = Literal["OPEN", "CLOSED", "CANCELLED"]


class TradeCreate(BaseModel):
    account_id: str
    strategy_id: str | None = None
    journal_id: str | None = None
    symbol: str = Field(min_length=1, max_length=20)
    side: TradeSide
    status: TradeStatus = "CLOSED"
    quantity: Decimal
    entry_price: Decimal
    exit_price: Decimal | None = None
    pnl: Decimal = Decimal("0")
    commission: Decimal = Decimal("0")
    notes: str | None = None
    tags: list[str] = []
    is_verified: bool = False
    opened_at: datetime
    closed_at: datetime | None = None


class TradeUpdate(BaseModel):
    strategy_id: str | None = None
    journal_id: str | None = None
    symbol: str | None = None
    side: TradeSide | None = None
    status: TradeStatus | None = None
    quantity: Decimal | None = None
    entry_price: Decimal | None = None
    exit_price: Decimal | None = None
    pnl: Decimal | None = None
    commission: Decimal | None = None
    notes: str | None = None
    tags: list[str] | None = None
    is_verified: bool | None = None
    opened_at: datetime | None = None
    closed_at: datetime | None = None


class TradeResponse(BaseModel):
    id: str
    account_id: str
    strategy_id: str | None
    journal_id: str | None
    symbol: str
    side: TradeSide
    status: TradeStatus
    quantity: Decimal
    entry_price: Decimal
    exit_price: Decimal | None
    pnl: Decimal
    commission: Decimal
    notes: str | None
    tags: list[str]
    is_verified: bool
    opened_at: datetime
    closed_at: datetime | None

    @classmethod
    def from_model(cls, t) -> "TradeResponse":
        return cls(
            id=t.id,
            account_id=t.accountId,
            strategy_id=t.strategyId,
            journal_id=t.journalId,
            symbol=t.symbol,
            side=t.side,
            status=t.status,
            quantity=t.quantity,
            entry_price=t.entryPrice,
            exit_price=t.exitPrice,
            pnl=t.pnl,
            commission=t.commission,
            notes=t.notes,
            tags=t.tags,
            is_verified=t.isVerified,
            opened_at=t.openedAt,
            closed_at=t.closedAt,
        )
