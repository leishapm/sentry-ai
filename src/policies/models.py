from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Enum, Index, String, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.enums import PolicySeverity
from src.db.base import Base, TimestampMixin


class Policy(TimestampMixin, Base):
    __tablename__ = "policy"
    __table_args__ = (
        Index("policy_enabled_severity_idx", "enabled", "severity"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    policy_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[PolicySeverity] = mapped_column(
        Enum(
            PolicySeverity,
            name="policy_severity",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        index=True,
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))

    audit_logs: Mapped[list["AuditLog"]] = relationship(
        back_populates="policy",
        passive_deletes=True,
    )
