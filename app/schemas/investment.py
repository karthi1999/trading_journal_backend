from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

InvestmentTypeLiteral = Literal[
    "STOCK_IN",
    "STOCK_US",
    "ETF_IN",
    "ETF_US",
    "MUTUAL_FUND",
    "GOLD_ETF",
    "GOLD_SGB",
    "GOLD_DIGITAL",
    "GOLD_PHYSICAL",
    "BOND",
]

Currency = Literal["INR", "USD"]


class InvestmentCreate(BaseModel):
    type: InvestmentTypeLiteral
    name: str = Field(min_length=1, max_length=120)
    symbol: str | None = None
    quantity: Decimal = Field(gt=0)
    avg_cost_price: Decimal = Field(ge=0)
    current_price: Decimal | None = Field(default=None, ge=0)
    currency: Currency = "INR"
    purchase_date: date | None = None
    maturity_date: date | None = None
    coupon_rate: Decimal | None = Field(default=None, ge=0, le=100)
    notes: str | None = None


class InvestmentUpdate(BaseModel):
    type: InvestmentTypeLiteral | None = None
    name: str | None = Field(default=None, min_length=1, max_length=120)
    symbol: str | None = None
    quantity: Decimal | None = Field(default=None, gt=0)
    avg_cost_price: Decimal | None = Field(default=None, ge=0)
    current_price: Decimal | None = Field(default=None, ge=0)
    currency: Currency | None = None
    purchase_date: date | None = None
    maturity_date: date | None = None
    coupon_rate: Decimal | None = Field(default=None, ge=0, le=100)
    notes: str | None = None


class InvestmentResponse(BaseModel):
    id: str
    type: InvestmentTypeLiteral
    name: str
    symbol: str | None
    quantity: Decimal
    avg_cost_price: Decimal
    current_price: Decimal | None
    currency: Currency
    purchase_date: date | None
    maturity_date: date | None
    coupon_rate: Decimal | None
    notes: str | None
    invested: Decimal
    current_value: Decimal | None
    pnl: Decimal | None
    pnl_percent: float | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, i) -> "InvestmentResponse":
        invested = (i.avg_cost_price or Decimal("0")) * (i.quantity or Decimal("0"))
        current_value = (
            (i.current_price * i.quantity)
            if (i.current_price is not None and i.quantity is not None)
            else None
        )
        pnl = (current_value - invested) if current_value is not None else None
        pnl_percent = (
            float(pnl / invested * Decimal("100"))
            if pnl is not None and invested > 0
            else None
        )
        return cls(
            id=i.id,
            type=i.type.value if hasattr(i.type, "value") else i.type,
            name=i.name,
            symbol=i.symbol,
            quantity=i.quantity,
            avg_cost_price=i.avg_cost_price,
            current_price=i.current_price,
            currency=i.currency,
            purchase_date=i.purchase_date,
            maturity_date=i.maturity_date,
            coupon_rate=i.coupon_rate,
            notes=i.notes,
            invested=invested,
            current_value=current_value,
            pnl=pnl,
            pnl_percent=pnl_percent,
            created_at=i.created_at,
            updated_at=i.updated_at,
        )


class AllocationSlice(BaseModel):
    label: str
    value: Decimal
    percent: float


class TopHolding(BaseModel):
    id: str
    name: str
    type: InvestmentTypeLiteral
    current_value: Decimal
    pnl: Decimal
    pnl_percent: float


class InvestmentSummary(BaseModel):
    home_currency: Currency
    has_unconvertible: bool
    invested_home: Decimal
    current_value_home: Decimal
    pnl_home: Decimal
    pnl_percent: float
    holdings_count: int
    by_type: list[AllocationSlice]
    by_currency: list[AllocationSlice]
    top_holdings: list[TopHolding]
    best_performer: TopHolding | None
    worst_performer: TopHolding | None
