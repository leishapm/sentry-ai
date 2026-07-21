from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

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

router = APIRouter(tags=["Execution"])


def get_execution_service() -> ExecutionService:
    return ExecutionService()


def get_audit_log_service() -> AuditLogService:
    return AuditLogService()


def get_approval_service() -> ApprovalService:
    return ApprovalService()


def get_policy_service() -> PolicyService:
    return PolicyService()


@router.post("/execute", response_model=ExecuteResponse)
async def execute_tool_request(
    request: ToolExecutionRequest,
    session: AsyncSession = Depends(get_session),
    service: ExecutionService = Depends(get_execution_service),
) -> ExecuteResponse:
    return await service.execute(session, request)


@router.get("/audit", response_model=AuditListResponse)
async def list_audit_logs(
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    service: AuditLogService = Depends(get_audit_log_service),
) -> AuditListResponse:
    return await service.list_recent(session, limit=limit, offset=offset)


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    session: AsyncSession = Depends(get_session),
    service: AuditLogService = Depends(get_audit_log_service),
) -> StatsResponse:
    return await service.get_stats(session)


@router.post("/approve/{approval_request_id}", response_model=ApprovalDecisionResponse)
async def decide_approval_request(
    approval_request_id: UUID,
    request: ApprovalDecisionRequest,
    session: AsyncSession = Depends(get_session),
    service: ApprovalService = Depends(get_approval_service),
) -> ApprovalDecisionResponse:
    approval_request = await service.decide(session, approval_request_id, request)
    if approval_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found.",
        )
    return ApprovalDecisionResponse.model_validate(approval_request)


@router.get("/policies", response_model=list[PolicyResponse])
async def list_policies(
    session: AsyncSession = Depends(get_session),
    service: PolicyService = Depends(get_policy_service),
) -> list[PolicyResponse]:
    return await service.list_active(session)

