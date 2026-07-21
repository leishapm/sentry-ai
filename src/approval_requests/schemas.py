from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.core.enums import ApprovalStatus


class ApprovalRequestBase(BaseModel):
    audit_log_id: UUID
    status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: str | None = Field(default=None, max_length=128)
    approved_at: datetime | None = None
    comments: str | None = None


class ApprovalRequestCreate(ApprovalRequestBase):
    pass


class ApprovalRequestUpdate(BaseModel):
    status: ApprovalStatus | None = None
    approved_by: str | None = Field(default=None, max_length=128)
    approved_at: datetime | None = None
    comments: str | None = None


class ApprovalRequestRead(ApprovalRequestBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
