from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

AccountType = Literal["LIVE", "DEMO", "PROP"]


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    broker_name: str | None = None
    account_number: str | None = None
    type: AccountType = "LIVE"
    balance: Decimal = Decimal("0")
    currency: str = "USD"


class AccountResponse(BaseModel):
    id: str
    name: str
    broker_name: str | None
    account_number: str | None
    type: AccountType
    balance: Decimal
    currency: str
    created_at: datetime

    @classmethod
    def from_model(cls, a) -> "AccountResponse":
        return cls(
            id=a.id,
            name=a.name,
            broker_name=a.broker_name,
            account_number=a.account_number,
            type=a.type,
            balance=a.balance,
            currency=a.currency,
            created_at=a.created_at,
        )
