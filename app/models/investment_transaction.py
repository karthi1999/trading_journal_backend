from datetime import date as date_
from datetime import datetime
from decimal import Decimal

import cuid
from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TransactionType


class InvestmentTransaction(Base):
    __tablename__ = "investment_transactions"
    __table_args__ = (
        Index("investment_transactions_userId_idx", "userId"),
        Index("investment_transactions_investmentId_idx", "investmentId"),
        Index(
            "investment_transactions_userId_transactionDate_idx",
            "userId",
            "transactionDate",
        ),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=cuid.cuid)
    user_id: Mapped[str] = mapped_column("userId", String, nullable=False)
    investment_id: Mapped[str] = mapped_column(
        "investmentId",
        String,
        ForeignKey("investments.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, name="TransactionType", create_type=False),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    fees: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )
    transaction_date: Mapped[date_] = mapped_column(
        "transactionDate", Date, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        "createdAt", DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    investment = relationship("Investment", back_populates="transactions")
