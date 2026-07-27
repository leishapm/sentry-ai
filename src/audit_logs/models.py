from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, SmallInteger, String, Text, Uuid, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.enums import ApprovalStatus, Decision
from src.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (
        CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="risk_score_range"),
        CheckConstraint(
            "execution_time_ms IS NULL OR execution_time_ms >= 0",
            name="execution_time_ms_non_negative",
        ),
        Index("audit_log_agent_tool_timestamp_idx", "agent_name", "tool_name", "timestamp"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    agent_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    tool_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(256), nullable=False)
    decision: Mapped[Decision] = mapped_column(
        Enum(
            Decision,
            name="sentry_decision",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        index=True,
    )
    risk_score: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0, server_default=text("0"))
    reason: Mapped[str | None] = mapped_column(Text)
    violated_policy: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("policy.policy_code", ondelete="SET NULL"),
        index=True,
    )
    suggested_fix: Mapped[str | None] = mapped_column(Text)
    execution_time_ms: Mapped[int | None] = mapped_column()
    request_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    response_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    policy: Mapped["Policy | None"] = relationship(
        back_populates="audit_logs",
        foreign_keys=[violated_policy],
    )
    approval_request: Mapped["ApprovalRequest | None"] = relationship(
        back_populates="audit_log",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )

    # Convenience accessors for AuditEntry serialization - the API needs to tell
    # callers whether a CONFIRM decision still has a pending approval (and its
    # id) so a dashboard can act on it. Callers must eager-load approval_request
    # (e.g. selectinload) since this is accessed outside of async-safe lazy load.
    @property
    def approval_request_id(self) -> uuid.UUID | None:
        return self.approval_request.id if self.approval_request else None

    @property
    def approval_status(self) -> ApprovalStatus | None:
        return self.approval_request.status if self.approval_request else None
