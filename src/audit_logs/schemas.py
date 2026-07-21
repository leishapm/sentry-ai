from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.core.enums import Decision


class AuditLogBase(BaseModel):
    agent_name: str = Field(min_length=1, max_length=128)
    tool_name: str = Field(min_length=1, max_length=128)
    action: str = Field(min_length=1, max_length=256)
    decision: Decision
    risk_score: int = Field(ge=0, le=100)
    reason: str | None = None
    violated_policy: str | None = Field(default=None, max_length=64)
    suggested_fix: str | None = None
    execution_time_ms: int | None = Field(default=None, ge=0)
    request_payload: dict[str, Any] | None = None
    response_payload: dict[str, Any] | None = None


class AuditLogCreate(AuditLogBase):
    pass


class AuditLogRead(AuditLogBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    timestamp: datetime

