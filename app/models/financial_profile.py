from datetime import datetime
from decimal import Decimal

import cuid
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FinancialProfile(Base):
    __tablename__ = "financial_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=cuid.cuid)
    user_id: Mapped[str] = mapped_column(
        "userId",
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    monthly_income: Mapped[Decimal | None] = mapped_column(
        "monthlyIncome", Numeric(18, 2), nullable=True
    )
    monthly_family_expense: Mapped[Decimal | None] = mapped_column(
        "monthlyFamilyExpense", Numeric(18, 2), nullable=True
    )
    monthly_savings: Mapped[Decimal | None] = mapped_column(
        "monthlySavings", Numeric(18, 2), nullable=True
    )
    currency: Mapped[str] = mapped_column(String, nullable=False, default="USD")
    usd_inr_rate: Mapped[Decimal | None] = mapped_column(
        "usdInrRate", Numeric(12, 4), nullable=True
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

    user = relationship("User", back_populates="financial_profile")
