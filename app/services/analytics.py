from collections import defaultdict
from datetime import date as date_
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import financial_profile as crud_profile
from app.crud import trade as crud_trade
from app.schemas.analytics import (
    CalendarDay,
    DashboardSummary,
    MarketBreakdownSlice,
    TimeseriesPoint,
    TradeBrief,
    WeeklyAggregate,
)


def _convert_to_home(
    amount: Decimal, from_ccy: str, home_ccy: str, usd_inr: Decimal | None
) -> Decimal:
    """Convert `amount` from `from_ccy` to `home_ccy`. Falls back to the raw value if
    the FX rate is missing — better than blocking the dashboard, the Settings page warns
    the user separately."""
    if from_ccy == home_ccy:
        return amount
    if usd_inr is None or usd_inr <= 0:
        return amount
    if from_ccy == "USD" and home_ccy == "INR":
        return amount * usd_inr
    if from_ccy == "INR" and home_ccy == "USD":
        return amount / usd_inr
    return amount


async def _load_fx_context(
    db: AsyncSession, user_id: str
) -> tuple[str, Decimal | None]:
    profile = await crud_profile.get_for_user(db, user_id)
    home = (
        profile.currency if profile and profile.currency in ("INR", "USD") else "INR"
    )
    rate = profile.usd_inr_rate if profile else None
    return home, rate


def _score(win_rate: float, profit_factor: float, trades: int) -> int:
    """Composite 0-100 score: win rate (0-40), profit factor (0-40), volume (0-20)."""
    wr = min(40.0, win_rate / 100.0 * 40.0)
    pf = min(40.0, profit_factor / 3.0 * 40.0) if profit_factor > 0 else 0.0
    vol = min(20.0, trades / 50.0 * 20.0)
    return int(round(wr + pf + vol))


async def compute_dashboard(
    db: AsyncSession,
    *,
    user_id: str,
    start: date_ | None,
    end: date_ | None,
    account_id: str | None,
    verified: bool | None,
    month: str | None = None,
) -> DashboardSummary:
    # If a `month` (YYYY-MM) is provided, override start/end to span that month.
    if month:
        try:
            y, m = month.split("-")
            year_i = int(y)
            month_i = int(m)
            month_start = date_(year_i, month_i, 1)
            next_month = (
                date_(year_i + 1, 1, 1) if month_i == 12 else date_(year_i, month_i + 1, 1)
            )
            start = month_start
            end = next_month - timedelta(days=1)
        except (ValueError, IndexError):
            pass  # ignore malformed month

    end_dt = (
        datetime.combine(end, time.max, tzinfo=timezone.utc) if end else datetime.now(timezone.utc)
    )
    start_dt = (
        datetime.combine(start, time.min, tzinfo=timezone.utc)
        if start
        else end_dt - timedelta(days=30)
    )

    trades = await crud_trade.list_closed_between(
        db,
        user_id=user_id,
        start=start_dt,
        end=end_dt,
        account_id=account_id,
        verified=verified,
    )
    home_ccy, fx = await _load_fx_context(db, user_id)

    total_pnl = Decimal("0")
    wins = losses = breakevens = 0
    gross_win = Decimal("0")
    gross_loss = Decimal("0")
    daily: dict[date_, Decimal] = defaultdict(lambda: Decimal("0"))
    daily_trades: dict[date_, dict] = defaultdict(
        lambda: {"trades": 0, "wins": 0, "losses": 0}
    )
    by_market: dict[str, dict] = defaultdict(lambda: {"trades": 0, "pnl": Decimal("0")})
    # Best/worst tracked in home currency so cross-currency comparisons are fair.
    best_pnl_home: Decimal | None = None
    worst_pnl_home: Decimal | None = None
    best_trade_ref = None
    worst_trade_ref = None

    for t in trades:
        pnl_home = _convert_to_home(t.pnl, t.currency, home_ccy, fx)
        total_pnl += pnl_home

        market_key = t.market.value if hasattr(t.market, "value") else str(t.market)
        by_market[market_key]["trades"] += 1
        by_market[market_key]["pnl"] += pnl_home
        if pnl_home > 0:
            wins += 1
            gross_win += pnl_home
        elif pnl_home < 0:
            losses += 1
            gross_loss += -pnl_home
        else:
            breakevens += 1

        if best_pnl_home is None or pnl_home > best_pnl_home:
            best_pnl_home = pnl_home
            best_trade_ref = t
        if worst_pnl_home is None or pnl_home < worst_pnl_home:
            worst_pnl_home = pnl_home
            worst_trade_ref = t

        if t.closed_at:
            d = t.closed_at.date()
            daily[d] += pnl_home
            daily_trades[d]["trades"] += 1
            if pnl_home > 0:
                daily_trades[d]["wins"] += 1
            elif pnl_home < 0:
                daily_trades[d]["losses"] += 1

    total = len(trades)
    win_rate = (wins / total * 100.0) if total else 0.0
    profit_factor = float(gross_win / gross_loss) if gross_loss > 0 else 0.0
    avg_win = (gross_win / wins) if wins else Decimal("0")
    avg_loss = (gross_loss / losses) if losses else Decimal("0")

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

    weekly_buckets: dict[date_, dict] = defaultdict(lambda: {"pnl": Decimal("0"), "trades": 0})
    for c in calendar:
        week_start = c.date - timedelta(days=(c.date.weekday() + 1) % 7)
        weekly_buckets[week_start]["pnl"] += c.pnl
        weekly_buckets[week_start]["trades"] += c.trades
    weekly = [
        WeeklyAggregate(week_start=k, pnl=v["pnl"], trades=v["trades"])
        for k, v in sorted(weekly_buckets.items())
    ]

    # Best/worst already picked above via home-currency comparison.
    best_brief = (
        TradeBrief(
            id=best_trade_ref.id,
            symbol=best_trade_ref.symbol,
            pnl=_convert_to_home(best_trade_ref.pnl, best_trade_ref.currency, home_ccy, fx),
            closed_at=best_trade_ref.closed_at.date() if best_trade_ref.closed_at else None,
        )
        if best_trade_ref
        else None
    )
    worst_brief = (
        TradeBrief(
            id=worst_trade_ref.id,
            symbol=worst_trade_ref.symbol,
            pnl=_convert_to_home(worst_trade_ref.pnl, worst_trade_ref.currency, home_ccy, fx),
            closed_at=worst_trade_ref.closed_at.date() if worst_trade_ref.closed_at else None,
        )
        if worst_trade_ref
        else None
    )

    market_slices = [
        MarketBreakdownSlice(market=k, trades=v["trades"], pnl=v["pnl"])
        for k, v in sorted(by_market.items(), key=lambda kv: -kv[1]["trades"])
    ]

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
        by_market=market_slices,
        best_trade=best_brief,
        worst_trade=worst_brief,
    )


async def compute_daily_summary(
    db: AsyncSession,
    *,
    user_id: str,
    days: int,
) -> list[dict]:
    """Returns raw bucket data; the API layer converts to DailyJournalSummary."""
    from app.crud import journal as crud_journal

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    trades = await crud_trade.list_closed_between(
        db, user_id=user_id, start=start, end=end
    )
    home_ccy, fx = await _load_fx_context(db, user_id)

    journals = await crud_journal.list_for_user(
        db, user_id=user_id, start=start.date(), end=end.date()
    )
    notes_by_date = {j.date: j.notes for j in journals}

    buckets: dict[date_, dict] = defaultdict(
        lambda: {
            "pnl": Decimal("0"),
            "trades": 0,
            "wins": 0,
            "losses": 0,
            "gross_win": Decimal("0"),
            "gross_loss": Decimal("0"),
            "commission": Decimal("0"),
        }
    )

    for t in trades:
        if not t.closed_at:
            continue
        d = t.closed_at.date()
        b = buckets[d]
        pnl_home = _convert_to_home(t.pnl, t.currency, home_ccy, fx)
        commission_home = _convert_to_home(t.commission, t.currency, home_ccy, fx)
        b["pnl"] += pnl_home
        b["trades"] += 1
        b["commission"] += commission_home
        if pnl_home > 0:
            b["wins"] += 1
            b["gross_win"] += pnl_home
        elif pnl_home < 0:
            b["losses"] += 1
            b["gross_loss"] += -pnl_home

    out: list[dict] = []
    for i in range(days):
        d = (end - timedelta(days=i)).date()
        b = buckets.get(d)
        notes = notes_by_date.get(d)
        if not b:
            out.append(
                {
                    "date": d,
                    "pnl": Decimal("0"),
                    "trades": 0,
                    "wins": 0,
                    "losses": 0,
                    "win_rate": 0.0,
                    "profit_factor": 0.0,
                    "commission": Decimal("0"),
                    "notes": notes,
                }
            )
            continue
        wr = (b["wins"] / b["trades"] * 100.0) if b["trades"] else 0.0
        pf = float(b["gross_win"] / b["gross_loss"]) if b["gross_loss"] > 0 else 0.0
        out.append(
            {
                "date": d,
                "pnl": b["pnl"],
                "trades": b["trades"],
                "wins": b["wins"],
                "losses": b["losses"],
                "win_rate": round(wr, 2),
                "profit_factor": round(pf, 2),
                "commission": b["commission"],
                "notes": notes,
            }
        )
    return out
