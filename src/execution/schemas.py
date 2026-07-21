from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.core.enums import ApprovalStatus, Decision, PolicySeverity


class ToolExecutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_name: str = Field(min_length=1, max_length=128)
    tool_name: str = Field(min_length=1, max_length=128)
    action: str = Field(min_length=1, max_length=256)
    parameters: dict[str, Any] = Field(default_factory=dict)
    requested_scope: str | None = Field(default=None, max_length=128)
    allowed_scopes: list[str] = Field(default_factory=list)
    estimated_cost_usd: float | None = Field(default=None, ge=0)
    is_irreversible: bool = False
    user_confirmed: bool = False
    recent_requests_count: int = Field(default=0, ge=0)
    context: dict[str, Any] = Field(default_factory=dict)


class RuleResult(BaseModel):
    rule: str
    policy_code: str
    passed: bool
    severity: PolicySeverity
    reason: str
    suggested_fix: str | None = None


class RiskAssessment(BaseModel):
    risk_score: int = Field(ge=0, le=100)
    decision: Decision
    reason: str
    violated_policy: str | None = None
    suggested_fix: str | None = None


class ExecuteResponse(RiskAssessment):
    audit_log_id: UUID
    approval_request_id: UUID | None = None
    rule_results: list[RuleResult]
    execution_time_ms: int


class AuditEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    timestamp: datetime
    agent_name: str
    tool_name: str
    action: str
    decision: Decision
    risk_score: int
    reason: str | None
    violated_policy: str | None
    suggested_fix: str | None
    execution_time_ms: int | None
    request_payload: dict[str, Any] | None
    response_payload: dict[str, Any] | None


class AuditListResponse(BaseModel):
    items: list[AuditEntry]
    total: int
    limit: int
    offset: int


class StatsResponse(BaseModel):
    total_requests: int
    allowed_requests: int
    blocked_requests: int
    confirmation_requests: int
    average_risk_score: float


class ApprovalDecisionRequest(BaseModel):
    status: ApprovalStatus
    approved_by: str = Field(min_length=1, max_length=128)
    comments: str | None = None

    @field_validator("status")
    @classmethod
    def status_must_be_terminal(cls, status: ApprovalStatus) -> ApprovalStatus:
        if status == ApprovalStatus.PENDING:
            raise ValueError("Approval status must be APPROVED or REJECTED.")
        return status


class ApprovalDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    audit_log_id: UUID
    status: ApprovalStatus
    approved_by: str | None
    approved_at: datetime | None
    comments: str | None


class PolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    policy_code: str
    name: str
    description: str
    severity: PolicySeverity
    enabled: bool
    created_at: datetime
    updated_at: datetime
