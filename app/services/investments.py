from collections import defaultdict
from datetime import date as date_
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import financial_profile as crud_profile
from app.crud import investment as crud_investment
from app.crud import investment_transaction as crud_tx
from app.models import Investment
from app.schemas.investment import (
    AllocationSlice,
    InvestmentSummary,
    TopHolding,
)
from app.schemas.investment_transaction import MonthlyBucket, MonthlySummary


def _convert(amount: Decimal, from_ccy: str, to_ccy: str, usd_inr: Decimal | None) -> Decimal | None:
    """Convert `amount` from `from_ccy` to `to_ccy`. Returns None if conversion needs an FX rate
    that isn't configured."""
    if from_ccy == to_ccy:
        return amount
    if usd_inr is None or usd_inr <= 0:
        return None
    if from_ccy == "USD" and to_ccy == "INR":
        return amount * usd_inr
    if from_ccy == "INR" and to_ccy == "USD":
        return amount / usd_inr
    return None


def _invested(i: Investment) -> Decimal:
    return (i.avg_cost_price or Decimal("0")) * (i.quantity or Decimal("0"))


def _current_value(i: Investment) -> Decimal | None:
    if i.current_price is None or i.quantity is None:
        return None
    return i.current_price * i.quantity


_TYPE_LABELS = {
    "STOCK_IN": "Indian Stocks",
    "STOCK_US": "US Stocks",
    "ETF_IN": "Indian ETFs",
    "ETF_US": "US ETFs",
    "MUTUAL_FUND": "Mutual Funds",
    "GOLD_ETF": "Gold ETF",
    "GOLD_SGB": "SGB",
    "GOLD_DIGITAL": "Digital Gold",
    "GOLD_PHYSICAL": "Physical Gold",
    "BOND": "Bonds",
}


async def compute_summary(db: AsyncSession, *, user_id: str) -> InvestmentSummary:
    profile = await crud_profile.get_for_user(db, user_id)
    home_ccy = profile.currency if profile and profile.currency in ("INR", "USD") else "INR"
    usd_inr = profile.usd_inr_rate if profile and profile.usd_inr_rate else None

    investments = await crud_investment.list_for_user(db, user_id)

    invested_home = Decimal("0")
    current_home = Decimal("0")
    has_unconvertible = False
    by_type_value: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    by_ccy_value: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    enriched: list[tuple[Investment, Decimal, Decimal | None]] = []

    for inv in investments:
        invested = _invested(inv)
        current = _current_value(inv) or invested  # if no current price, fall back to cost
        enriched.append((inv, invested, _current_value(inv)))

        invested_h = _convert(invested, inv.currency, home_ccy, usd_inr)
        current_h = _convert(current, inv.currency, home_ccy, usd_inr)

        if invested_h is None or current_h is None:
            has_unconvertible = True
            continue

        invested_home += invested_h
        current_home += current_h
        type_key = inv.type.value if hasattr(inv.type, "value") else str(inv.type)
        by_type_value[type_key] += current_h
        by_ccy_value[inv.currency] += current_h

    pnl_home = current_home - invested_home
    pnl_percent = float(pnl_home / invested_home * Decimal("100")) if invested_home > 0 else 0.0

    by_type = _slices(by_type_value, label_map=_TYPE_LABELS)
    by_currency = _slices(by_ccy_value)

    # Top / best / worst — only over convertible holdings with a current price
    perf: list[TopHolding] = []
    for inv, invested, current_value in enriched:
        if current_value is None:
            continue
        current_h = _convert(current_value, inv.currency, home_ccy, usd_inr)
        invested_h = _convert(invested, inv.currency, home_ccy, usd_inr)
        if current_h is None or invested_h is None:
            continue
        pnl = current_h - invested_h
        pnl_pct = float(pnl / invested_h * Decimal("100")) if invested_h > 0 else 0.0
        perf.append(
            TopHolding(
                id=inv.id,
                name=inv.name,
                type=inv.type.value if hasattr(inv.type, "value") else str(inv.type),
                current_value=current_h,
                pnl=pnl,
                pnl_percent=pnl_pct,
            )
        )

    top_holdings = sorted(perf, key=lambda h: h.current_value, reverse=True)[:5]
    best = max(perf, key=lambda h: h.pnl_percent, default=None) if perf else None
    worst = min(perf, key=lambda h: h.pnl_percent, default=None) if perf else None

    return InvestmentSummary(
        home_currency=home_ccy,
        has_unconvertible=has_unconvertible,
        invested_home=invested_home,
        current_value_home=current_home,
        pnl_home=pnl_home,
        pnl_percent=round(pnl_percent, 2),
        holdings_count=len(investments),
        by_type=by_type,
        by_currency=by_currency,
        top_holdings=top_holdings,
        best_performer=best,
        worst_performer=worst,
    )


def _slices(
    totals: dict[str, Decimal], *, label_map: dict[str, str] | None = None
) -> list[AllocationSlice]:
    total = sum(totals.values(), start=Decimal("0"))
    if total <= 0:
        return []
    slices = [
        AllocationSlice(
            label=(label_map or {}).get(k, k),
            value=v,
            percent=round(float(v / total * Decimal("100")), 2),
        )
        for k, v in totals.items()
        if v > 0
    ]
    slices.sort(key=lambda s: s.value, reverse=True)
    return slices


def apply_buy(inv: Investment, qty: Decimal, price: Decimal) -> None:
    """Update the parent investment's qty + weighted avg cost after a BUY.
    Mutates `inv` in place; caller is responsible for committing the session."""
    old_qty = inv.quantity or Decimal("0")
    old_avg = inv.avg_cost_price or Decimal("0")
    new_qty = old_qty + qty
    if new_qty > 0:
        inv.avg_cost_price = (old_qty * old_avg + qty * price) / new_qty
    inv.quantity = new_qty


def apply_sell(inv: Investment, qty: Decimal) -> None:
    """Reduce the parent investment's qty after a SELL. Average cost is unchanged —
    selling doesn't affect cost basis. Quantity is clamped to 0."""
    old_qty = inv.quantity or Decimal("0")
    new_qty = old_qty - qty
    if new_qty < 0:
        new_qty = Decimal("0")
    inv.quantity = new_qty


async def compute_monthly_summary(
    db: AsyncSession,
    *,
    user_id: str,
    months: int,
) -> MonthlySummary:
    """Aggregate investment transactions into per-month invested / sold totals,
    converted to the user's profile currency."""
    today = date_.today()
    # First day of the window: `months` calendar months back from today.
    year = today.year
    month = today.month - (months - 1)
    while month <= 0:
        month += 12
        year -= 1
    start = date_(year, month, 1)

    profile = await crud_profile.get_for_user(db, user_id)
    home_ccy = (
        profile.currency if profile and profile.currency in ("INR", "USD") else "INR"
    )
    usd_inr = profile.usd_inr_rate if profile else None

    transactions = await crud_tx.list_for_user(db, user_id=user_id, start=start)

    buckets: dict[str, dict] = defaultdict(
        lambda: {
            "invested": Decimal("0"),
            "sold": Decimal("0"),
            "buy_count": 0,
            "sell_count": 0,
        }
    )

    for tx in transactions:
        amount_native = (tx.quantity or Decimal("0")) * (tx.price or Decimal("0"))
        ccy = tx.investment.currency if tx.investment else home_ccy
        amount_home = _convert(amount_native, ccy, home_ccy, usd_inr)
        if amount_home is None:
            # FX rate missing — fall back to native amount so users see something.
            amount_home = amount_native

        key = f"{tx.transaction_date.year}-{tx.transaction_date.month:02d}"
        b = buckets[key]
        is_buy = (tx.type.value if hasattr(tx.type, "value") else str(tx.type)) == "BUY"
        if is_buy:
            b["invested"] += amount_home
            b["buy_count"] += 1
        else:
            b["sold"] += amount_home
            b["sell_count"] += 1

    # Materialize every month in the window, even empty ones, so the chart
    # has a continuous x-axis.
    out: list[MonthlyBucket] = []
    cursor = start
    for _ in range(months):
        key = f"{cursor.year}-{cursor.month:02d}"
        b = buckets.get(
            key,
            {
                "invested": Decimal("0"),
                "sold": Decimal("0"),
                "buy_count": 0,
                "sell_count": 0,
            },
        )
        out.append(
            MonthlyBucket(
                month=key,
                invested=b["invested"],
                sold=b["sold"],
                net=b["invested"] - b["sold"],
                buy_count=b["buy_count"],
                sell_count=b["sell_count"],
            )
        )
        # Advance one month.
        next_month = cursor.month + 1
        next_year = cursor.year
        if next_month > 12:
            next_month = 1
            next_year += 1
        cursor = date_(next_year, next_month, 1)

    return MonthlySummary(home_currency=home_ccy, months=out)
