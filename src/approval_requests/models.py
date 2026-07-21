from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.enums import ApprovalStatus
from src.db.base import Base, TimestampMixin


class ApprovalRequest(TimestampMixin, Base):
    __tablename__ = "approval_request"
    __table_args__ = (
        Index("approval_request_status_created_idx", "status", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    audit_log_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("audit_log.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(
            ApprovalStatus,
            name="approval_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=ApprovalStatus.PENDING,
        server_default=text("'PENDING'"),
    )
    approved_by: Mapped[str | None] = mapped_column(String(128))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    comments: Mapped[str | None] = mapped_column(Text)

    audit_log: Mapped["AuditLog"] = relationship(back_populates="approval_request")
