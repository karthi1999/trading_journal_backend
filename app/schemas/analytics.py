from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class TimeseriesPoint(BaseModel):
    date: date
    value: Decimal


class CalendarDay(BaseModel):
    date: date
    pnl: Decimal
    trades: int
    wins: int
    losses: int


class WeeklyAggregate(BaseModel):
    week_start: date
    pnl: Decimal
    trades: int


class TradeBrief(BaseModel):
    id: str
    symbol: str
    pnl: Decimal
    closed_at: date | None


class MarketBreakdownSlice(BaseModel):
    market: str
    trades: int
    pnl: Decimal


class DashboardSummary(BaseModel):
    pnl: Decimal
    trades: int
    profit_factor: float
    win_rate: float
    wins: int
    losses: int
    breakevens: int
    avg_win: Decimal
    avg_loss: Decimal
    score: int
    cumulative_pnl: list[TimeseriesPoint]
    drawdown: list[TimeseriesPoint]
    daily_pnl: list[TimeseriesPoint]
    calendar: list[CalendarDay]
    weekly: list[WeeklyAggregate]
    by_market: list[MarketBreakdownSlice]
    best_trade: TradeBrief | None
    worst_trade: TradeBrief | None
