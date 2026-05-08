from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user
from app.db import prisma
from app.schemas.analytics import (
    CalendarDay,
    DashboardSummary,
    TimeseriesPoint,
    TradeBrief,
    WeeklyAggregate,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _score(win_rate: float, profit_factor: float, trades: int) -> int:
    """Composite 0-100 score: win rate (0-40), profit factor (0-40), volume (0-20)."""
    wr = min(40.0, win_rate / 100.0 * 40.0)
    pf = min(40.0, profit_factor / 3.0 * 40.0) if profit_factor > 0 else 0.0
    vol = min(20.0, trades / 50.0 * 20.0)
    return int(round(wr + pf + vol))


@router.get("/dashboard", response_model=DashboardSummary)
async def dashboard(
    user=Depends(get_current_user),
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    account_id: str | None = Query(default=None),
    verified: bool | None = Query(default=None),
) -> DashboardSummary:
    end_dt = datetime.combine(end, time.max, tzinfo=timezone.utc) if end else datetime.now(timezone.utc)
    start_dt = (
        datetime.combine(start, time.min, tzinfo=timezone.utc)
        if start
        else end_dt - timedelta(days=30)
    )

    where: dict = {
        "userId": user.id,
        "closedAt": {"gte": start_dt, "lte": end_dt, "not": None},
    }
    if account_id:
        where["accountId"] = account_id
    if verified is not None:
        where["isVerified"] = verified

    trades = await prisma.trade.find_many(where=where, order={"closedAt": "asc"})

    total_pnl = Decimal("0")
    wins = losses = breakevens = 0
    gross_win = Decimal("0")
    gross_loss = Decimal("0")
    daily: dict[date, Decimal] = defaultdict(lambda: Decimal("0"))
    daily_trades: dict[date, dict] = defaultdict(
        lambda: {"trades": 0, "wins": 0, "losses": 0}
    )

    for t in trades:
        total_pnl += t.pnl
        if t.pnl > 0:
            wins += 1
            gross_win += t.pnl
        elif t.pnl < 0:
            losses += 1
            gross_loss += -t.pnl
        else:
            breakevens += 1

        if t.closedAt:
            d = t.closedAt.date()
            daily[d] += t.pnl
            daily_trades[d]["trades"] += 1
            if t.pnl > 0:
                daily_trades[d]["wins"] += 1
            elif t.pnl < 0:
                daily_trades[d]["losses"] += 1

    total = len(trades)
    win_rate = (wins / total * 100.0) if total else 0.0
    profit_factor = float(gross_win / gross_loss) if gross_loss > 0 else 0.0
    avg_win = (gross_win / wins) if wins else Decimal("0")
    avg_loss = (gross_loss / losses) if losses else Decimal("0")

    # Cumulative PNL + drawdown
    days_span = (end_dt.date() - start_dt.date()).days + 1
    cumulative: list[TimeseriesPoint] = []
    drawdown_series: list[TimeseriesPoint] = []
    daily_pnl: list[TimeseriesPoint] = []
    running = Decimal("0")
    peak = Decimal("0")
    for i in range(max(days_span, 1)):
        d = start_dt.date() + timedelta(days=i)
        day_value = daily.get(d, Decimal("0"))
        running += day_value
        peak = max(peak, running)
        cumulative.append(TimeseriesPoint(date=d, value=running))
        drawdown_series.append(TimeseriesPoint(date=d, value=(running - peak)))
        daily_pnl.append(TimeseriesPoint(date=d, value=day_value))

    # Calendar (current month, derived from end_dt)
    cal_start = end_dt.replace(day=1).date()
    next_month = (end_dt.replace(day=28) + timedelta(days=4)).replace(day=1).date()
    cal_days_count = (next_month - cal_start).days
    calendar: list[CalendarDay] = []
    for i in range(cal_days_count):
        d = cal_start + timedelta(days=i)
        b = daily_trades.get(d, {"trades": 0, "wins": 0, "losses": 0})
        calendar.append(
            CalendarDay(
                date=d,
                pnl=daily.get(d, Decimal("0")),
                trades=b["trades"],
                wins=b["wins"],
                losses=b["losses"],
            )
        )

    # Weekly aggregates within month
    weekly_buckets: dict[date, dict] = defaultdict(lambda: {"pnl": Decimal("0"), "trades": 0})
    for c in calendar:
        week_start = c.date - timedelta(days=(c.date.weekday() + 1) % 7)
        weekly_buckets[week_start]["pnl"] += c.pnl
        weekly_buckets[week_start]["trades"] += c.trades
    weekly = [
        WeeklyAggregate(week_start=k, pnl=v["pnl"], trades=v["trades"])
        for k, v in sorted(weekly_buckets.items())
    ]

    # Best / worst
    best = max(trades, key=lambda t: t.pnl, default=None)
    worst = min(trades, key=lambda t: t.pnl, default=None)
    best_brief = (
        TradeBrief(
            id=best.id,
            symbol=best.symbol,
            pnl=best.pnl,
            closed_at=best.closedAt.date() if best.closedAt else None,
        )
        if best
        else None
    )
    worst_brief = (
        TradeBrief(
            id=worst.id,
            symbol=worst.symbol,
            pnl=worst.pnl,
            closed_at=worst.closedAt.date() if worst.closedAt else None,
        )
        if worst
        else None
    )

    return DashboardSummary(
        pnl=total_pnl,
        trades=total,
        profit_factor=round(profit_factor, 2),
        win_rate=round(win_rate, 2),
        wins=wins,
        losses=losses,
        breakevens=breakevens,
        avg_win=avg_win,
        avg_loss=avg_loss,
        score=_score(win_rate, profit_factor, total),
        cumulative_pnl=cumulative,
        drawdown=drawdown_series,
        daily_pnl=daily_pnl,
        calendar=calendar,
        weekly=weekly,
        best_trade=best_brief,
        worst_trade=worst_brief,
    )
