import random
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import account as crud_account
from app.crud import expense as crud_expense
from app.crud import investment as crud_investment
from app.crud import investment_transaction as crud_tx
from app.crud import trade as crud_trade
from app.models import (
    Account,
    AccountType,
    ExpenseCategory,
    InvestmentType,
    MarketType,
    TradeSide,
    TradeStatus,
    TransactionType,
)

# Symbol -> (price low, price high, point value).
# Point value is rough — only used to make pnl-from-price math feel realistic.
_SYMBOLS: dict[str, tuple[float, float, float]] = {
    "MNQ": (18000, 21500, 2.0),
    "NQ": (18000, 21500, 20.0),
    "ES": (4500, 5500, 50.0),
    "MES": (4500, 5500, 5.0),
    "YM": (38000, 42500, 5.0),
    "RTY": (2000, 2400, 50.0),
    "CL": (70, 92, 1000.0),
    "GC": (2300, 2700, 100.0),
}


async def _ensure_account(db: AsyncSession, user_id: str) -> Account:
    accounts = await crud_account.list_for_user(db, user_id)
    if accounts:
        return accounts[0]
    return await crud_account.create(
        db,
        user_id=user_id,
        name="Demo Account",
        broker_name="Demo Broker",
        account_number=None,
        type=AccountType.DEMO,
        balance=Decimal("10000.00"),
        currency="USD",
    )


async def seed_trades(
    db: AsyncSession,
    *,
    user_id: str,
    days: int,
    count: int,
    seed: int,
) -> dict:
    account = await _ensure_account(db, user_id)
    await crud_trade.delete_all_for_user(db, user_id)

    rng = random.Random(seed)
    now = datetime.now(timezone.utc)
    created = 0

    for _ in range(count):
        symbol = rng.choice(list(_SYMBOLS.keys()))
        low, high, point_value = _SYMBOLS[symbol]
        side = rng.choice([TradeSide.LONG, TradeSide.SHORT])

        day_offset = rng.randint(0, days)
        opened = now - timedelta(
            days=day_offset,
            hours=rng.randint(0, 6),
            minutes=rng.randint(0, 59),
        )
        opened = opened.replace(hour=rng.randint(13, 19), minute=rng.randint(0, 59), second=0)
        while opened.weekday() >= 5:
            opened -= timedelta(days=1)

        duration_min = rng.randint(2, 240)
        closed = opened + timedelta(minutes=duration_min)

        entry_price = round(rng.uniform(low, high), 2)
        qty = rng.randint(1, 5)

        is_win = rng.random() < 0.6
        if is_win:
            pnl = round(rng.uniform(25, 500), 2)
        else:
            pnl = -round(rng.uniform(20, 400), 2)

        direction = 1 if side == TradeSide.LONG else -1
        price_delta = pnl / max(1, qty) / point_value * 4
        exit_price = round(entry_price + price_delta * direction, 2)
        if exit_price <= 0:
            exit_price = round(entry_price * 0.95, 2)

        commission = round(rng.uniform(1.0, 5.0), 2)

        await crud_trade.create(
            db,
            user_id=user_id,
            account_id=account.id,
            strategy_id=None,
            journal_id=None,
            symbol=symbol,
            side=side,
            status=TradeStatus.CLOSED,
            quantity=Decimal(str(qty)),
            entry_price=Decimal(str(entry_price)),
            exit_price=Decimal(str(exit_price)),
            pnl=Decimal(str(pnl)),
            commission=Decimal(str(commission)),
            currency="USD",
            market=MarketType.COMMODITY if symbol in ("CL", "GC") else MarketType.STOCK,
            notes=None,
            tags=[],
            is_verified=rng.random() < 0.7,
            opened_at=opened,
            closed_at=closed,
        )
        created += 1

    return {"created": created, "account": account.name, "days": days}


# Realistic-looking sample holdings across all 10 asset types.
# (type, name, symbol, qty, avg_cost, current_price, currency, purchase_offset_days,
#  maturity_offset_days, coupon_rate, notes)
_DEMO_INVESTMENTS: list[tuple] = [
    (InvestmentType.STOCK_IN, "Reliance Industries", "RELIANCE", 12, 2450.00, 2890.50, "INR", 420, None, None, None),
    (InvestmentType.STOCK_IN, "TCS", "TCS", 8, 3520.00, 3760.25, "INR", 280, None, None, None),
    (InvestmentType.STOCK_IN, "HDFC Bank", "HDFCBANK", 15, 1480.00, 1655.80, "INR", 510, None, None, None),
    (InvestmentType.STOCK_IN, "Infosys", "INFY", 20, 1320.00, 1410.40, "INR", 200, None, None, None),
    (InvestmentType.ETF_IN, "Nippon India ETF Nifty BeES", "NIFTYBEES", 50, 245.00, 268.75, "INR", 365, None, None, None),
    (InvestmentType.ETF_IN, "ICICI Pru Nifty Next 50 ETF", "ICICINXT50", 40, 58.30, 64.10, "INR", 180, None, None, None),
    (InvestmentType.MUTUAL_FUND, "Parag Parikh Flexi Cap", "122639", 250.456, 62.80, 78.20, "INR", 600, None, None, "Direct Growth"),
    (InvestmentType.MUTUAL_FUND, "Axis Bluechip Fund", "120465", 180.221, 48.50, 54.90, "INR", 420, None, None, "Direct Growth"),
    (InvestmentType.MUTUAL_FUND, "SBI Small Cap Fund", "125354", 95.105, 110.20, 142.60, "INR", 700, None, None, "Direct Growth"),
    (InvestmentType.STOCK_US, "Apple Inc", "AAPL", 6, 175.20, 218.40, "USD", 320, None, None, None),
    (InvestmentType.STOCK_US, "Microsoft", "MSFT", 4, 380.00, 432.10, "USD", 240, None, None, None),
    (InvestmentType.STOCK_US, "NVIDIA", "NVDA", 5, 420.00, 138.50, "USD", 150, None, None, "Post-split; cost basis adjusted"),
    (InvestmentType.ETF_US, "Vanguard S&P 500", "VOO", 3, 410.00, 498.20, "USD", 540, None, None, None),
    (InvestmentType.ETF_US, "Invesco QQQ", "QQQ", 2, 360.00, 478.90, "USD", 440, None, None, None),
    (InvestmentType.GOLD_ETF, "Nippon India Gold BeES", "GOLDBEES", 120, 52.80, 68.40, "INR", 600, None, None, None),
    (InvestmentType.GOLD_SGB, "SGB 2023-24 Series IV", "SGBNOV31", 10, 6149.00, 7280.00, "INR", 730, 2920, 2.5, "Matures 2031; 2.5% semi-annual interest"),
    (InvestmentType.GOLD_DIGITAL, "Digital Gold (PhonePe)", None, 4.5, 6200.00, 7280.00, "INR", 200, None, None, "In grams"),
    (InvestmentType.GOLD_PHYSICAL, "24K Gold Coins (10g)", None, 30, 5950.00, 7280.00, "INR", 900, None, None, "Locker stored; per gram"),
    (InvestmentType.BOND, "HDFC Ltd NCD 2027", "HDFC27", 50, 1000.00, 1052.00, "INR", 480, 1095, 7.85, "Semi-annual coupon"),
    (InvestmentType.BOND, "Govt of India 7.18% 2033", "718GOI33", 100, 985.00, 1018.50, "INR", 300, 2920, 7.18, None),
]


async def seed_investments(db: AsyncSession, *, user_id: str) -> dict:
    """Wipe and recreate a representative set of demo investments for the user.
    Each holding gets a synthetic transaction history (3–6 monthly buys) so the
    monthly investment chart has meaningful data."""
    await crud_investment.delete_all_for_user(db, user_id)

    rng = random.Random(11)
    today = date.today()
    created = 0
    tx_count = 0
    for (
        i_type,
        name,
        symbol,
        qty,
        avg_cost,
        current_price,
        currency,
        purchase_offset,
        maturity_offset,
        coupon_rate,
        notes,
    ) in _DEMO_INVESTMENTS:
        # Create the investment with zero qty/avg cost; the seeded transactions
        # below will accumulate to roughly the demo target.
        inv = await crud_investment.create(
            db,
            user_id=user_id,
            fields={
                "type": i_type,
                "name": name,
                "symbol": symbol,
                "quantity": Decimal("0"),
                "avg_cost_price": Decimal("0"),
                "current_price": Decimal(str(current_price)),
                "currency": currency,
                "purchase_date": today - timedelta(days=purchase_offset),
                "maturity_date": (
                    today + timedelta(days=maturity_offset)
                    if maturity_offset is not None
                    else None
                ),
                "coupon_rate": (
                    Decimal(str(coupon_rate)) if coupon_rate is not None else None
                ),
                "notes": notes,
            },
        )
        created += 1

        # Build 3–6 BUY transactions distributed across the last 12 months,
        # summing to the target quantity, with prices jittered around avg_cost.
        n_buys = rng.randint(3, 6)
        weights = [rng.uniform(0.5, 1.5) for _ in range(n_buys)]
        total_weight = sum(weights)
        target = Decimal(str(qty))

        for idx in range(n_buys):
            # Quantity slice — last slice gets the remainder to avoid drift.
            if idx == n_buys - 1:
                slice_qty = target - inv.quantity
            else:
                slice_qty = (
                    target * Decimal(str(weights[idx]))
                    / Decimal(str(total_weight))
                ).quantize(Decimal("0.0001"))
            if slice_qty <= 0:
                continue

            price_jitter = rng.uniform(0.85, 1.15)
            tx_price = Decimal(str(round(avg_cost * price_jitter, 4)))
            months_ago = rng.randint(0, 11)
            day_of_month = rng.randint(1, 28)

            # Compute tx_date roughly months_ago months back.
            year = today.year
            month = today.month - months_ago
            while month <= 0:
                month += 12
                year -= 1
            tx_date = date(year, month, day_of_month)

            # Update the parent investment's qty + weighted avg cost.
            from app.services.investments import apply_buy  # local import to avoid cycle

            apply_buy(inv, slice_qty, tx_price)
            await crud_tx.create(
                db,
                user_id=user_id,
                investment=inv,
                tx_type=TransactionType.BUY,
                quantity=slice_qty,
                price=tx_price,
                fees=Decimal("0"),
                transaction_date=tx_date,
                notes=None,
            )
            tx_count += 1

    return {"created": created, "transactions": tx_count}


# (category, description, min, max, currency, monthly_recurrence_chance)
# Mixes recurring/large items (rent, EMI) with frequent small ones (groceries, dining)
# so the monthly chart shows realistic variance.
_DEMO_EXPENSE_TEMPLATES: list[tuple] = [
    # (category, description, min_amt, max_amt, monthly_chance, recurring)
    (ExpenseCategory.HOUSING, "Apartment rent", 22000, 22000, 1.0, True),
    (ExpenseCategory.UTILITIES, "Electricity bill", 1200, 2400, 1.0, True),
    (ExpenseCategory.UTILITIES, "Internet (broadband)", 999, 999, 1.0, True),
    (ExpenseCategory.SUBSCRIPTIONS, "Netflix", 649, 649, 1.0, True),
    (ExpenseCategory.SUBSCRIPTIONS, "Spotify Premium", 119, 119, 1.0, True),
    (ExpenseCategory.SUBSCRIPTIONS, "iCloud storage", 75, 75, 1.0, True),
    (ExpenseCategory.FOOD, "Groceries", 4500, 8500, 1.0, False),
    (ExpenseCategory.FOOD, "Dining out", 600, 1800, 0.85, False),
    (ExpenseCategory.FOOD, "Swiggy / Zomato", 350, 900, 0.7, False),
    (ExpenseCategory.TRANSPORT, "Fuel", 2200, 4200, 0.9, False),
    (ExpenseCategory.TRANSPORT, "Uber / Ola", 180, 700, 0.6, False),
    (ExpenseCategory.HEALTHCARE, "Pharmacy", 400, 1500, 0.4, False),
    (ExpenseCategory.SHOPPING, "Amazon order", 800, 4500, 0.7, False),
    (ExpenseCategory.SHOPPING, "Clothing", 1500, 5000, 0.3, False),
    (ExpenseCategory.ENTERTAINMENT, "Movie tickets", 400, 1100, 0.4, False),
    (ExpenseCategory.TRAVEL, "Weekend getaway", 3500, 12000, 0.15, False),
    (ExpenseCategory.EDUCATION, "Online course", 1200, 3500, 0.1, False),
]


async def seed_expenses(db: AsyncSession, *, user_id: str) -> dict:
    """Wipe and recreate ~9 months of plausible personal expenses for the user."""
    await crud_expense.delete_all_for_user(db, user_id)

    rng = random.Random(31)
    today = date.today()
    months_back = 9
    created = 0

    for i in range(months_back):
        # Compute first day of the target month, `i` months ago.
        year = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year -= 1
        first = date(year, month, 1)

        for category, description, lo, hi, chance, recurring in _DEMO_EXPENSE_TEMPLATES:
            if rng.random() > chance:
                continue

            # Recurring entries land near the same day of month; one-offs are random.
            if recurring:
                day = min(rng.randint(1, 5), 28)
            else:
                day = rng.randint(1, 28)

            # If this is the current month, don't seed dates after today.
            if year == today.year and month == today.month and day > today.day:
                day = today.day

            amount = round(rng.uniform(lo, hi), 2)
            await crud_expense.create(
                db,
                user_id=user_id,
                fields={
                    "category": category,
                    "amount": Decimal(str(amount)),
                    "currency": "INR",
                    "expense_date": date(first.year, first.month, day),
                    "description": description,
                    "recurring": recurring,
                },
            )
            created += 1

    return {"created": created}
