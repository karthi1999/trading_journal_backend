from datetime import datetime
from decimal import Decimal

import cuid
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Numeric, String, func, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import MarketType, TradeSide, TradeStatus


class Trade(Base):
    __tablename__ = "trades"
    __table_args__ = (
        Index("trades_userId_openedAt_idx", "userId", "openedAt"),
        Index("trades_userId_closedAt_idx", "userId", "closedAt"),
        Index("trades_accountId_idx", "accountId"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=cuid.cuid)
    user_id: Mapped[str] = mapped_column(
        "userId", String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[str] = mapped_column(
        "accountId", String, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    strategy_id: Mapped[str | None] = mapped_column(
        "strategyId",
        String,
        ForeignKey("strategies.id", ondelete="SET NULL"),
        nullable=True,
    )
    journal_id: Mapped[str | None] = mapped_column(
        "journalId",
        String,
        ForeignKey("daily_journals.id", ondelete="SET NULL"),
        nullable=True,
    )
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    side: Mapped[TradeSide] = mapped_column(
        Enum(TradeSide, name="TradeSide", create_type=False), nullable=False
    )
    status: Mapped[TradeStatus] = mapped_column(
        Enum(TradeStatus, name="TradeStatus", create_type=False),
        nullable=False,
        default=TradeStatus.CLOSED,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    entry_price: Mapped[Decimal] = mapped_column("entryPrice", Numeric(18, 8), nullable=False)
    exit_price: Mapped[Decimal | None] = mapped_column(
        "exitPrice", Numeric(18, 8), nullable=True
    )
    pnl: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )
    commission: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )
    currency: Mapped[str] = mapped_column(String, nullable=False, default="USD")
    market: Mapped[MarketType] = mapped_column(
        Enum(MarketType, name="MarketType", create_type=False),
        nullable=False,
        default=MarketType.STOCK,
    )
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        server_default=text("ARRAY[]::text[]"),
        default=list,
    )
    is_verified: Mapped[bool] = mapped_column(
        "isVerified", Boolean, nullable=False, default=False
    )
    opened_at: Mapped[datetime] = mapped_column("openedAt", DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(
        "closedAt", DateTime(timezone=True), nullable=True
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

    user = relationship("User", back_populates="trades")
    account = relationship("Account", back_populates="trades")
    strategy = relationship("Strategy", back_populates="trades")
    journal = relationship("DailyJournal", back_populates="trades")
    attachments = relationship(
        "TradeAttachment", back_populates="trade", cascade="all, delete-orphan"
    )
