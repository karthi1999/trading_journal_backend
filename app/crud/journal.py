from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DailyJournal


async def list_for_user(
    db: AsyncSession,
    *,
    user_id: str,
    start: date | None = None,
    end: date | None = None,
) -> list[DailyJournal]:
    stmt = select(DailyJournal).where(DailyJournal.user_id == user_id)
    if start:
        stmt = stmt.where(DailyJournal.date >= start)
    if end:
        stmt = stmt.where(DailyJournal.date <= end)
    stmt = stmt.order_by(DailyJournal.date.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get(db: AsyncSession, journal_id: str) -> DailyJournal | None:
    return await db.get(DailyJournal, journal_id)


async def upsert(
    db: AsyncSession,
    *,
    user_id: str,
    day: date,
    notes: str | None,
    mood: str | None,
) -> DailyJournal:
    stmt = (
        insert(DailyJournal)
        .values(user_id=user_id, date=day, notes=notes, mood=mood)
        .on_conflict_do_update(
            constraint="daily_journals_userId_date_key",
            set_={"notes": notes, "mood": mood},
        )
        .returning(DailyJournal)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one()


async def delete(db: AsyncSession, journal: DailyJournal) -> None:
    await db.delete(journal)
    await db.commit()
