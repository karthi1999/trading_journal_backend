from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_current_user
from app.db import prisma
from app.schemas.journal import DailyJournalSummary, JournalResponse, JournalUpsert

router = APIRouter(prefix="/journals", tags=["journals"])


@router.get("", response_model=list[JournalResponse])
async def list_journals(
    user=Depends(get_current_user),
    start: date | None = None,
    end: date | None = None,
) -> list[JournalResponse]:
    where: dict = {"userId": user.id}
    if start or end:
        where["date"] = {}
        if start:
            where["date"]["gte"] = datetime.combine(start, time.min, tzinfo=timezone.utc)
        if end:
            where["date"]["lte"] = datetime.combine(end, time.max, tzinfo=timezone.utc)

    items = await prisma.dailyjournal.find_many(where=where, order={"date": "desc"})
    return [JournalResponse.from_model(j) for j in items]


@router.put("", response_model=JournalResponse)
async def upsert_journal(
    payload: JournalUpsert, user=Depends(get_current_user)
) -> JournalResponse:
    day = datetime.combine(payload.date, time.min, tzinfo=timezone.utc)
    j = await prisma.dailyjournal.upsert(
        where={"userId_date": {"userId": user.id, "date": day}},
        data={
            "create": {
                "userId": user.id,
                "date": day,
                "notes": payload.notes,
                "mood": payload.mood,
            },
            "update": {"notes": payload.notes, "mood": payload.mood},
        },
    )
    return JournalResponse.from_model(j)


@router.delete("/{journal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_journal(journal_id: str, user=Depends(get_current_user)) -> None:
    j = await prisma.dailyjournal.find_unique(where={"id": journal_id})
    if not j or j.userId != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal not found")
    await prisma.dailyjournal.delete(where={"id": journal_id})


@router.get("/daily-summary", response_model=list[DailyJournalSummary])
async def daily_summary(
    user=Depends(get_current_user),
    days: int = Query(default=14, ge=1, le=365),
) -> list[DailyJournalSummary]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    trades = await prisma.trade.find_many(
        where={
            "userId": user.id,
            "closedAt": {"gte": start, "lte": end, "not": None},
        },
        order={"closedAt": "desc"},
    )

    journals = await prisma.dailyjournal.find_many(
        where={"userId": user.id, "date": {"gte": start, "lte": end}}
    )
    notes_by_date = {
        (j.date.date() if isinstance(j.date, datetime) else j.date): j.notes for j in journals
    }

    buckets: dict[date, dict] = defaultdict(
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
        if not t.closedAt:
            continue
        d = t.closedAt.date()
        b = buckets[d]
        b["pnl"] += t.pnl
        b["trades"] += 1
        b["commission"] += t.commission
        if t.pnl > 0:
            b["wins"] += 1
            b["gross_win"] += t.pnl
        elif t.pnl < 0:
            b["losses"] += 1
            b["gross_loss"] += -t.pnl

    out: list[DailyJournalSummary] = []
    for i in range(days):
        d = (end - timedelta(days=i)).date()
        b = buckets.get(d)
        if not b:
            out.append(
                DailyJournalSummary(
                    date=d,
                    pnl=Decimal("0"),
                    trades=0,
                    wins=0,
                    losses=0,
                    win_rate=0.0,
                    profit_factor=0.0,
                    commission=Decimal("0"),
                    notes=notes_by_date.get(d),
                )
            )
            continue
        wr = (b["wins"] / b["trades"] * 100.0) if b["trades"] else 0.0
        pf = float(b["gross_win"] / b["gross_loss"]) if b["gross_loss"] > 0 else 0.0
        out.append(
            DailyJournalSummary(
                date=d,
                pnl=b["pnl"],
                trades=b["trades"],
                wins=b["wins"],
                losses=b["losses"],
                win_rate=round(wr, 2),
                profit_factor=round(pf, 2),
                commission=b["commission"],
                notes=notes_by_date.get(d),
            )
        )
    return out
