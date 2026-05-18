from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.crud import journal as crud_journal
from app.db import get_db
from app.schemas.journal import DailyJournalSummary, JournalResponse, JournalUpsert
from app.services import analytics as analytics_service

router = APIRouter(prefix="/journals", tags=["journals"])


@router.get("", response_model=list[JournalResponse])
async def list_journals(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    start: date | None = None,
    end: date | None = None,
) -> list[JournalResponse]:
    items = await crud_journal.list_for_user(db, user_id=user.id, start=start, end=end)
    return [JournalResponse.from_model(j) for j in items]


@router.put("", response_model=JournalResponse)
async def upsert_journal(
    payload: JournalUpsert,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JournalResponse:
    j = await crud_journal.upsert(
        db,
        user_id=user.id,
        day=payload.date,
        notes=payload.notes,
        mood=payload.mood,
    )
    return JournalResponse.from_model(j)


@router.delete("/{journal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_journal(
    journal_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    j = await crud_journal.get(db, journal_id)
    if not j or j.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal not found")
    await crud_journal.delete(db, j)


@router.get("/daily-summary", response_model=list[DailyJournalSummary])
async def daily_summary(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    days: int = Query(default=14, ge=1, le=365),
) -> list[DailyJournalSummary]:
    rows = await analytics_service.compute_daily_summary(db, user_id=user.id, days=days)
    return [DailyJournalSummary(**row) for row in rows]
