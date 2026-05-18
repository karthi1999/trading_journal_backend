from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.attachment import AttachmentResponse

TradeSide = Literal["LONG", "SHORT"]
TradeStatus = Literal["OPEN", "CLOSED", "CANCELLED"]
Currency = Literal["INR", "USD"]
MarketTypeLiteral = Literal["STOCK", "FOREX", "COMMODITY", "CRYPTO"]


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
    currency: Currency = "USD"
    market: MarketTypeLiteral = "STOCK"
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
    currency: Currency | None = None
    market: MarketTypeLiteral | None = None
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
    currency: Currency
    market: MarketTypeLiteral
    notes: str | None
    tags: list[str]
    is_verified: bool
    opened_at: datetime
    closed_at: datetime | None
    attachments: list[AttachmentResponse] = []

    @classmethod
    def from_model(cls, t) -> "TradeResponse":
        return cls(
            id=t.id,
            account_id=t.account_id,
            strategy_id=t.strategy_id,
            journal_id=t.journal_id,
            symbol=t.symbol,
            side=t.side,
            status=t.status,
            quantity=t.quantity,
            entry_price=t.entry_price,
            exit_price=t.exit_price,
            pnl=t.pnl,
            commission=t.commission,
            currency=t.currency if t.currency in ("INR", "USD") else "USD",
            market=(t.market.value if hasattr(t.market, "value") else str(t.market)),
            notes=t.notes,
            tags=t.tags,
            is_verified=t.is_verified,
            opened_at=t.opened_at,
            closed_at=t.closed_at,
            attachments=[AttachmentResponse.from_model(a) for a in (t.attachments or [])],
        )
