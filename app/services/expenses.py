from collections import defaultdict
from datetime import date as date_
from datetime import timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import expense as crud_expense
from app.crud import financial_profile as crud_profile
from app.schemas.expense import (
    CategoryBucket,
    ExpenseSummary,
    MonthlyExpenseBucket,
)


def _convert_to_home(
    amount: Decimal, from_ccy: str, home_ccy: str, usd_inr: Decimal | None
) -> Decimal:
    if from_ccy == home_ccy:
        return amount
    if usd_inr is None or usd_inr <= 0:
        return amount  # silent fallback; settings shows a warning separately
    if from_ccy == "USD" and home_ccy == "INR":
        return amount * usd_inr
    if from_ccy == "INR" and home_ccy == "USD":
        return amount / usd_inr
    return amount


def _start_of_month_n_back(today: date_, months: int) -> date_:
    year = today.year
    month = today.month - (months - 1)
    while month <= 0:
        month += 12
        year -= 1
    return date_(year, month, 1)


async def compute_summary(
    db: AsyncSession,
    *,
    user_id: str,
    months: int,
) -> ExpenseSummary:
    today = date_.today()
    window_start = _start_of_month_n_back(today, months)

    profile = await crud_profile.get_for_user(db, user_id)
    home_ccy = (
        profile.currency if profile and profile.currency in ("INR", "USD") else "INR"
    )
    usd_inr = profile.usd_inr_rate if profile else None

    expenses = await crud_expense.list_for_user(
        db, user_id=user_id, start=window_start, limit=10000
    )

    monthly_totals: dict[str, dict] = defaultdict(
        lambda: {"amount": Decimal("0"), "count": 0}
    )
    category_totals: dict[str, dict] = defaultdict(
        lambda: {"amount": Decimal("0"), "count": 0}
    )

    this_month_key = f"{today.year}-{today.month:02d}"
    last_month_dt = today.replace(day=1) - timedelta(days=1)
    last_month_key = f"{last_month_dt.year}-{last_month_dt.month:02d}"

    this_month_total = Decimal("0")
    last_month_total = Decimal("0")
    total_window = Decimal("0")
    count_window = 0

    for e in expenses:
        amount_home = _convert_to_home(e.amount, e.currency, home_ccy, usd_inr)
        key = f"{e.expense_date.year}-{e.expense_date.month:02d}"
        monthly_totals[key]["amount"] += amount_home
        monthly_totals[key]["count"] += 1

        cat = e.category.value if hasattr(e.category, "value") else str(e.category)
        category_totals[cat]["amount"] += amount_home
        category_totals[cat]["count"] += 1

        total_window += amount_home
        count_window += 1
        if key == this_month_key:
            this_month_total += amount_home
        elif key == last_month_key:
            last_month_total += amount_home

    # Materialize every month in the window so the chart x-axis is continuous.
    months_out: list[MonthlyExpenseBucket] = []
    cursor = window_start
    for _ in range(months):
        key = f"{cursor.year}-{cursor.month:02d}"
        b = monthly_totals.get(key, {"amount": Decimal("0"), "count": 0})
        months_out.append(
            MonthlyExpenseBucket(month=key, amount=b["amount"], count=b["count"])
        )
        next_month = cursor.month + 1
        next_year = cursor.year
        if next_month > 12:
            next_month = 1
            next_year += 1
        cursor = date_(next_year, next_month, 1)

    by_category = [
        CategoryBucket(category=cat, amount=v["amount"], count=v["count"])
        for cat, v in sorted(
            category_totals.items(), key=lambda kv: -kv[1]["amount"]
        )
    ]

    avg_monthly = total_window / Decimal(months) if months > 0 else Decimal("0")

    return ExpenseSummary(
        home_currency=home_ccy,
        months=months_out,
        by_category=by_category,
        this_month_total=this_month_total,
        last_month_total=last_month_total,
        avg_monthly=avg_monthly,
        total_window=total_window,
        count_window=count_window,
    )
