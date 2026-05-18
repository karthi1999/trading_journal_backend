from datetime import datetime
from decimal import Decimal

import cuid
from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AccountType


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (Index("accounts_userId_idx", "userId"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=cuid.cuid)
    user_id: Mapped[str] = mapped_column(
        "userId", String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    broker_name: Mapped[str | None] = mapped_column("brokerName", String, nullable=True)
    account_number: Mapped[str | None] = mapped_column("accountNumber", String, nullable=True)
    type: Mapped[AccountType] = mapped_column(
        Enum(AccountType, name="AccountType", create_type=False),
        nullable=False,
        default=AccountType.LIVE,
    )
    balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )
    currency: Mapped[str] = mapped_column(String, nullable=False, default="USD")
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

    user = relationship("User", back_populates="accounts")
    trades = relationship("Trade", back_populates="account", cascade="all, delete-orphan")
