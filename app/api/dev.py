import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user
from app.db import prisma

router = APIRouter(prefix="/dev", tags=["dev"])

# Symbol -> (price low, price high, point value, tick step)
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


@router.post("/seed-trades")
async def seed_trades(
    user=Depends(get_current_user),
    days: int = Query(default=30, ge=1, le=365),
    count: int = Query(default=60, ge=1, le=500),
    seed: int = Query(default=42),
) -> dict:
    """Generate demo trades for the current user. Idempotent — wipes existing trades first."""
    accounts = await prisma.account.find_many(where={"userId": user.id})
    if accounts:
        account = accounts[0]
    else:
        account = await prisma.account.create(
            data={
                "userId": user.id,
                "name": "Demo Account",
                "brokerName": "Demo Broker",
                "type": "DEMO",
                "balance": Decimal("10000.00"),
                "currency": "USD",
            }
        )

    # Make seeding repeatable: clear out any prior demo trades for this user.
    await prisma.trade.delete_many(where={"userId": user.id})

    rng = random.Random(seed)
    now = datetime.now(timezone.utc)
    created = 0

    for _ in range(count):
        symbol = rng.choice(list(_SYMBOLS.keys()))
        low, high, point_value = _SYMBOLS[symbol]
        side = rng.choice(["LONG", "SHORT"])

        # Random weekday in the last `days`.
        day_offset = rng.randint(0, days)
        opened = now - timedelta(
            days=day_offset,
            hours=rng.randint(0, 6),
            minutes=rng.randint(0, 59),
        )
        # Snap to a typical trading hour (09:30–15:55 ET ≈ 13:30–19:55 UTC).
        opened = opened.replace(hour=rng.randint(13, 19), minute=rng.randint(0, 59), second=0)
        while opened.weekday() >= 5:
            opened -= timedelta(days=1)

        duration_min = rng.randint(2, 240)
        closed = opened + timedelta(minutes=duration_min)

        entry_price = round(rng.uniform(low, high), 2)
        qty = rng.randint(1, 5)

        # 60% win rate, with realistic pnl ranges.
        is_win = rng.random() < 0.6
        if is_win:
            pnl = round(rng.uniform(25, 500), 2)
        else:
            pnl = -round(rng.uniform(20, 400), 2)

        # Back-solve exit price from pnl so the row is self-consistent.
        direction = 1 if side == "LONG" else -1
        price_delta = pnl / max(1, qty) / point_value * 4  # rough scaling
        exit_price = round(entry_price + price_delta * direction, 2)
        if exit_price <= 0:
            exit_price = round(entry_price * 0.95, 2)

        commission = round(rng.uniform(1.0, 5.0), 2)

        await prisma.trade.create(
            data={
                "userId": user.id,
                "accountId": account.id,
                "symbol": symbol,
                "side": side,
                "status": "CLOSED",
                "quantity": Decimal(str(qty)),
                "entryPrice": Decimal(str(entry_price)),
                "exitPrice": Decimal(str(exit_price)),
                "pnl": Decimal(str(pnl)),
                "commission": Decimal(str(commission)),
                "openedAt": opened,
                "closedAt": closed,
                "isVerified": rng.random() < 0.7,
            }
        )
        created += 1

    return {"created": created, "account": account.name, "days": days}


@router.delete("/clear-trades")
async def clear_trades(user=Depends(get_current_user)) -> dict:
    """Wipe all trades for the current user."""
    res = await prisma.trade.delete_many(where={"userId": user.id})
    return {"deleted": res}
