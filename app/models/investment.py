from datetime import date as date_
from datetime import datetime
from decimal import Decimal

import cuid
from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import InvestmentType


class Investment(Base):
    __tablename__ = "investments"
    __table_args__ = (
        Index("investments_userId_idx", "userId"),
        Index("investments_userId_type_idx", "userId", "type"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=cuid.cuid)
    user_id: Mapped[str] = mapped_column(
        "userId", String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[InvestmentType] = mapped_column(
        Enum(InvestmentType, name="InvestmentType", create_type=False),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    symbol: Mapped[str | None] = mapped_column(String, nullable=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    avg_cost_price: Mapped[Decimal] = mapped_column(
        "avgCostPrice", Numeric(18, 4), nullable=False
    )
    current_price: Mapped[Decimal | None] = mapped_column(
        "currentPrice", Numeric(18, 4), nullable=True
    )
    currency: Mapped[str] = mapped_column(String, nullable=False, default="INR")
    purchase_date: Mapped[date_ | None] = mapped_column(
        "purchaseDate", Date, nullable=True
    )
    maturity_date: Mapped[date_ | None] = mapped_column(
        "maturityDate", Date, nullable=True
    )
    coupon_rate: Mapped[Decimal | None] = mapped_column(
        "couponRate", Numeric(6, 3), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
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

    user = relationship("User", back_populates="investments")
    transactions = relationship(
        "InvestmentTransaction",
        back_populates="investment",
        cascade="all, delete-orphan",
        order_by="InvestmentTransaction.transaction_date.desc()",
    )
