from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

TransactionTypeLiteral = Literal["BUY", "SELL"]


class TransactionCreate(BaseModel):
    type: TransactionTypeLiteral
    quantity: Decimal = Field(gt=0)
    price: Decimal = Field(ge=0)
    fees: Decimal = Field(default=Decimal("0"), ge=0)
    transaction_date: date
    notes: str | None = None


class TransactionResponse(BaseModel):
    id: str
    investment_id: str
    type: TransactionTypeLiteral
    quantity: Decimal
    price: Decimal
    fees: Decimal
    amount: Decimal  # quantity * price (cost basis component, excludes fees)
    transaction_date: date
    notes: str | None
    created_at: datetime

    @classmethod
    def from_model(cls, t) -> "TransactionResponse":
        amount = (t.quantity or Decimal("0")) * (t.price or Decimal("0"))
        return cls(
            id=t.id,
            investment_id=t.investment_id,
            type=t.type.value if hasattr(t.type, "value") else str(t.type),
            quantity=t.quantity,
            price=t.price,
            fees=t.fees,
            amount=amount,
            transaction_date=t.transaction_date,
            notes=t.notes,
            created_at=t.created_at,
        )


class MonthlyBucket(BaseModel):
    """One calendar month's totals, in the user's profile currency."""

    month: str  # YYYY-MM
    invested: Decimal
    sold: Decimal
    net: Decimal  # invested - sold
    buy_count: int
    sell_count: int


class MonthlySummary(BaseModel):
    home_currency: Literal["INR", "USD"]
    months: list[MonthlyBucket]
