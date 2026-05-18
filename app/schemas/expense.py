from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

ExpenseCategoryLiteral = Literal[
    "FOOD",
    "HOUSING",
    "TRANSPORT",
    "UTILITIES",
    "ENTERTAINMENT",
    "SHOPPING",
    "HEALTHCARE",
    "EDUCATION",
    "SUBSCRIPTIONS",
    "TRAVEL",
    "OTHER",
]

Currency = Literal["INR", "USD"]


class ExpenseCreate(BaseModel):
    category: ExpenseCategoryLiteral = "OTHER"
    amount: Decimal = Field(gt=0)
    currency: Currency = "INR"
    expense_date: date
    description: str | None = None
    recurring: bool = False


class ExpenseUpdate(BaseModel):
    category: ExpenseCategoryLiteral | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    currency: Currency | None = None
    expense_date: date | None = None
    description: str | None = None
    recurring: bool | None = None


class ExpenseResponse(BaseModel):
    id: str
    category: ExpenseCategoryLiteral
    amount: Decimal
    currency: Currency
    expense_date: date
    description: str | None
    recurring: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, e) -> "ExpenseResponse":
        return cls(
            id=e.id,
            category=e.category.value if hasattr(e.category, "value") else str(e.category),
            amount=e.amount,
            currency=e.currency if e.currency in ("INR", "USD") else "INR",
            expense_date=e.expense_date,
            description=e.description,
            recurring=e.recurring,
            created_at=e.created_at,
            updated_at=e.updated_at,
        )


class CategoryBucket(BaseModel):
    category: ExpenseCategoryLiteral
    amount: Decimal  # total in home currency
    count: int


class MonthlyExpenseBucket(BaseModel):
    month: str  # YYYY-MM
    amount: Decimal  # total in home currency
    count: int


class ExpenseSummary(BaseModel):
    home_currency: Currency
    months: list[MonthlyExpenseBucket]
    by_category: list[CategoryBucket]
    this_month_total: Decimal
    last_month_total: Decimal
    avg_monthly: Decimal  # over the requested window
    total_window: Decimal
    count_window: int
