from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

Currency = Literal["INR", "USD"]


class FinancialProfileUpsert(BaseModel):
    age: int | None = Field(default=None, ge=0, le=150)
    monthly_income: Decimal | None = Field(default=None, ge=0)
    monthly_family_expense: Decimal | None = Field(default=None, ge=0)
    monthly_savings: Decimal | None = Field(default=None, ge=0)
    currency: Currency = "USD"
    usd_inr_rate: Decimal | None = Field(default=None, gt=0)


class FinancialProfileResponse(BaseModel):
    age: int | None
    monthly_income: Decimal | None
    monthly_family_expense: Decimal | None
    monthly_savings: Decimal | None
    currency: Currency
    usd_inr_rate: Decimal | None
    updated_at: datetime

    @classmethod
    def from_model(cls, p) -> "FinancialProfileResponse":
        return cls(
            age=p.age,
            monthly_income=p.monthly_income,
            monthly_family_expense=p.monthly_family_expense,
            monthly_savings=p.monthly_savings,
            currency=p.currency,
            usd_inr_rate=p.usd_inr_rate,
            updated_at=p.updated_at,
        )
