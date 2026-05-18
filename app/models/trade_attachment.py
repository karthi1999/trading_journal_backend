from datetime import datetime

import cuid
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TradeAttachment(Base):
    __tablename__ = "trade_attachments"
    __table_args__ = (
        Index("trade_attachments_tradeId_idx", "tradeId"),
        Index("trade_attachments_userId_idx", "userId"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=cuid.cuid)
    trade_id: Mapped[str] = mapped_column(
        "tradeId",
        String,
        ForeignKey("trades.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column("userId", String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    mime_type: Mapped[str] = mapped_column("mimeType", String, nullable=False)
    size_bytes: Mapped[int] = mapped_column("sizeBytes", Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        "createdAt", DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    trade = relationship("Trade", back_populates="attachments")
