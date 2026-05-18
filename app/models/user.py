from datetime import datetime

import cuid
from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=cuid.cuid)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column("passwordHash", String, nullable=False)
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

    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="user", cascade="all, delete-orphan")
    journals = relationship("DailyJournal", back_populates="user", cascade="all, delete-orphan")
    strategies = relationship("Strategy", back_populates="user", cascade="all, delete-orphan")
    connections = relationship("Connection", back_populates="user", cascade="all, delete-orphan")
    financial_profile = relationship(
        "FinancialProfile",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    investments = relationship(
        "Investment", back_populates="user", cascade="all, delete-orphan"
    )
    expenses = relationship(
        "Expense", back_populates="user", cascade="all, delete-orphan"
    )
