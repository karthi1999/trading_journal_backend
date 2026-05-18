from datetime import date as date_, datetime

import cuid
from sqlalchemy import Date, DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DailyJournal(Base):
    __tablename__ = "daily_journals"
    __table_args__ = (
        UniqueConstraint("userId", "date", name="daily_journals_userId_date_key"),
        Index("daily_journals_userId_idx", "userId"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=cuid.cuid)
    user_id: Mapped[str] = mapped_column(
        "userId", String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date_] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    mood: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        "createdAt", DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updatedAt",
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="journals")
    trades = relationship("Trade", back_populates="journal")
