from datetime import date as date_
from datetime import datetime
from decimal import Decimal

import cuid
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ExpenseCategory


class Expense(Base):
    __tablename__ = "expenses"
    __table_args__ = (
        Index("expenses_userId_idx", "userId"),
        Index("expenses_userId_expenseDate_idx", "userId", "expenseDate"),
        Index("expenses_userId_category_idx", "userId", "category"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=cuid.cuid)
    user_id: Mapped[str] = mapped_column(
        "userId", String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[ExpenseCategory] = mapped_column(
        Enum(ExpenseCategory, name="ExpenseCategory", create_type=False),
        nullable=False,
        default=ExpenseCategory.OTHER,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False, default="INR")
    expense_date: Mapped[date_] = mapped_column("expenseDate", Date, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    recurring: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
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

    user = relationship("User", back_populates="expenses")
