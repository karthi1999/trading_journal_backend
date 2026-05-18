from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class JournalUpsert(BaseModel):
    date: date
    notes: str | None = None
    mood: str | None = None


class JournalResponse(BaseModel):
    id: str
    date: date
    notes: str | None
    mood: str | None
    created_at: datetime

    @classmethod
    def from_model(cls, j) -> "JournalResponse":
        return cls(
            id=j.id,
            date=j.date.date() if isinstance(j.date, datetime) else j.date,
            notes=j.notes,
            mood=j.mood,
            created_at=j.created_at,
        )


class DailyJournalSummary(BaseModel):
    date: date
    pnl: Decimal
    trades: int
    wins: int
    losses: int
    win_rate: float
    profit_factor: float
    commission: Decimal
    notes: str | None = None
