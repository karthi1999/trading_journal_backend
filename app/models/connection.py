from datetime import datetime
from typing import Any

import cuid
from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ConnectionStatus


class Connection(Base):
    __tablename__ = "connections"
    __table_args__ = (Index("connections_userId_idx", "userId"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=cuid.cuid)
    user_id: Mapped[str] = mapped_column(
        "userId", String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    broker_name: Mapped[str] = mapped_column("brokerName", String, nullable=False)
    status: Mapped[ConnectionStatus] = mapped_column(
        Enum(ConnectionStatus, name="ConnectionStatus", create_type=False),
        nullable=False,
        default=ConnectionStatus.PENDING,
    )
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB, nullable=True)
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

    user = relationship("User", back_populates="connections")
