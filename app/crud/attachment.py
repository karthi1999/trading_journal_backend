from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TradeAttachment


async def list_for_trade(db: AsyncSession, trade_id: str) -> list[TradeAttachment]:
    result = await db.execute(
        select(TradeAttachment)
        .where(TradeAttachment.trade_id == trade_id)
        .order_by(TradeAttachment.created_at.asc())
    )
    return list(result.scalars().all())


async def get(db: AsyncSession, attachment_id: str) -> TradeAttachment | None:
    return await db.get(TradeAttachment, attachment_id)


async def create(
    db: AsyncSession,
    *,
    trade_id: str,
    user_id: str,
    url: str,
    filename: str,
    mime_type: str,
    size_bytes: int,
) -> TradeAttachment:
    attachment = TradeAttachment(
        trade_id=trade_id,
        user_id=user_id,
        url=url,
        filename=filename,
        mime_type=mime_type,
        size_bytes=size_bytes,
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)
    return attachment


async def delete(db: AsyncSession, attachment: TradeAttachment) -> None:
    await db.delete(attachment)
    await db.commit()
