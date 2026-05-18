from datetime import datetime
from typing import Any

import cuid
from sqlalchemy import DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Strategy(Base):
    __tablename__ = "strategies"
    __table_args__ = (Index("strategies_userId_idx", "userId"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=cuid.cuid)
    user_id: Mapped[str] = mapped_column(
        "userId", String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    entry_criteria: Mapped[list[Any]] = mapped_column(
        "entryCriteria",
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
        default=list,
    )
    exit_criteria: Mapped[list[Any]] = mapped_column(
        "exitCriteria",
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
        default=list,
    )
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

    user = relationship("User", back_populates="strategies")
    trades = relationship("Trade", back_populates="strategy")
