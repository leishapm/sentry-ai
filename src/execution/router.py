from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import Decision
from src.core.exceptions import EntityNotFoundException
from src.db.session import get_session
from src.execution.schemas import (
    ApprovalDecisionRequest,
    ApprovalDecisionResponse,
    AuditListResponse,
    ExecuteResponse,
    PolicyResponse,
    StatsResponse,
    ToolExecutionRequest,
)
from src.execution.services import (
    ApprovalService,
    AuditLogService,
    ExecutionService,
    PolicyService,
)

router = APIRouter(tags=["Execution & Audit"])


def get_execution_service() -> ExecutionService:
    return ExecutionService()


def get_audit_log_service() -> AuditLogService:
    return AuditLogService()


def get_approval_service() -> ApprovalService:
    return ApprovalService()


def get_policy_service() -> PolicyService:
    return PolicyService()


@router.post(
    "/execute",
    response_model=ExecuteResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate AI Execution Request",
    description="Evaluates an agent tool call request through SENTRY rule engine & AI reasoning layer, returning risk score, policy decision, and audit ID.",
)
async def execute_tool_request(
    request: ToolExecutionRequest,
    session: AsyncSession = Depends(get_session),
    service: ExecutionService = Depends(get_execution_service),
) -> ExecuteResponse:
    return await service.execute(session, request)


@router.get(
    "/audit",
    response_model=AuditListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Execution Audit Logs",
    description="Retrieves paginated audit log entries with optional filters for agent name, tool name, decision, and minimum risk score.",
)
async def list_audit_logs(
    limit: int = Query(default=25, ge=1, le=100, description="Max number of items per page."),
    offset: int = Query(default=0, ge=0, description="Page offset index."),
    agent_name: str | None = Query(default=None, description="Filter logs by agent name."),
    tool_name: str | None = Query(default=None, description="Filter logs by tool name."),
    decision: Decision | None = Query(default=None, description="Filter logs by decision outcome."),
    min_risk_score: int | None = Query(default=None, ge=0, le=100, description="Filter logs with risk score >= value."),
    session: AsyncSession = Depends(get_session),
    service: AuditLogService = Depends(get_audit_log_service),
) -> AuditListResponse:
    return await service.list_recent(
        session,
        limit=limit,
        offset=offset,
        agent_name=agent_name,
        tool_name=tool_name,
        decision=decision,
        min_risk_score=min_risk_score,
    )


@router.get(
    "/stats",
    response_model=StatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Execution Dashboard Statistics",
    description="Returns aggregated summary metrics across all recorded executions for firewall dashboards.",
)
async def get_stats(
    session: AsyncSession = Depends(get_session),
    service: AuditLogService = Depends(get_audit_log_service),
) -> StatsResponse:
    return await service.get_stats(session)


@router.post(
    "/approve/{approval_request_id}",
    response_model=ApprovalDecisionResponse,
    status_code=status.HTTP_200_OK,
    summary="Decide Approval Request",
    description="Updates the status of a pending approval request to APPROVED or REJECTED with human reviewer attribution.",
)
async def decide_approval_request(
    approval_request_id: UUID,
    request: ApprovalDecisionRequest,
    session: AsyncSession = Depends(get_session),
    service: ApprovalService = Depends(get_approval_service),
) -> ApprovalDecisionResponse:
    approval_request = await service.decide(session, approval_request_id, request)
    if approval_request is None:
        raise EntityNotFoundException(
            message=f"Approval request '{approval_request_id}' not found.",
        )
    return ApprovalDecisionResponse.model_validate(approval_request)


@router.get(
    "/policies",
    response_model=list[PolicyResponse],
    status_code=status.HTTP_200_OK,
    summary="List Active Security Policies",
    description="Returns all active security firewall policies ordered by severity.",
)
async def list_policies(
    session: AsyncSession = Depends(get_session),
    service: PolicyService = Depends(get_policy_service),
) -> list[PolicyResponse]:
    return await service.list_active(session)
