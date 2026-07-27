from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.core.enums import ApprovalStatus, Decision, PolicySeverity


class ToolExecutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_name: str = Field(min_length=1, max_length=128, description="Name or identifier of the AI agent.")
    tool_name: str = Field(min_length=1, max_length=128, description="Target tool being called.")
    action: str = Field(min_length=1, max_length=256, description="Action or function name to be executed.")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Parameters passed to the tool.")
    requested_scope: str | None = Field(default=None, max_length=128, description="Scope requested for this action.")
    allowed_scopes: list[str] = Field(default_factory=list, description="List of scopes authorized for this agent.")
    estimated_cost_usd: float | None = Field(default=None, ge=0, description="Estimated execution cost in USD.")
    is_irreversible: bool = Field(default=False, description="Whether the action cannot be undone.")
    user_confirmed: bool = Field(default=False, description="Whether explicit user confirmation was obtained.")
    recent_requests_count: int = Field(default=0, ge=0, description="Recent request count for rate limiting.")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional execution context metadata.")


class RuleResult(BaseModel):
    rule: str = Field(description="Name of the rule evaluated.")
    policy_code: str = Field(description="Policy code corresponding to this rule.")
    passed: bool = Field(description="True if rule passed, False if violated.")
    severity: PolicySeverity = Field(description="Severity level of the rule.")
    reason: str = Field(description="Detailed result explanation.")
    suggested_fix: str | None = Field(default=None, description="Suggested mitigation or fix.")


class RiskAssessment(BaseModel):
    risk_score: int = Field(ge=0, le=100, description="Calculated risk score from 0 to 100.")
    decision: Decision = Field(description="Final decision: ALLOW, CONFIRM, or BLOCK.")
    reason: str = Field(description="Detailed decision reasoning.")
    violated_policy: str | None = Field(default=None, description="Primary violated policy code.")
    suggested_fix: str | None = Field(default=None, description="Suggested resolution/fix.")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="AI reasoning confidence score.")


class ExecuteResponse(RiskAssessment):
    audit_log_id: UUID = Field(description="Unique ID of created audit log entry.")
    approval_request_id: UUID | None = Field(default=None, description="Approval request ID if decision is CONFIRM.")
    rule_results: list[RuleResult] = Field(description="Full list of evaluated rule results.")
    execution_time_ms: int = Field(description="Total policy evaluation duration in milliseconds.")


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
    approval_request_id: UUID | None = None
    approval_status: ApprovalStatus | None = None


class AuditListResponse(BaseModel):
    items: list[AuditEntry] = Field(description="List of audit log entries.")
    total: int = Field(description="Total count matching query filters.")
    limit: int = Field(description="Number of records requested per page.")
    offset: int = Field(description="Number of records skipped.")


class StatsResponse(BaseModel):
    total_requests: int = Field(description="Total number of execution requests logged.")
    allowed_requests: int = Field(description="Number of requests allowed.")
    blocked_requests: int = Field(description="Number of requests blocked.")
    confirmation_requests: int = Field(description="Number of requests requiring human approval.")
    average_risk_score: float = Field(description="Average risk score across all recorded executions.")
    average_execution_time_ms: float = Field(default=0.0, description="Average execution processing duration in ms.")
    high_risk_requests: int = Field(default=0, description="Number of requests with risk score >= 70.")


class ApprovalDecisionRequest(BaseModel):
    status: ApprovalStatus
    approved_by: str = Field(min_length=1, max_length=128, description="User or service making the decision.")
    comments: str | None = Field(default=None, description="Optional notes or justification.")

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
