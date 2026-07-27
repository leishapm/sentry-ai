from time import perf_counter
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.approval_requests.models import ApprovalRequest
from src.audit_logs.models import AuditLog
from src.core.enums import ApprovalStatus, Decision
from src.execution.risk_engine import RiskEngine
from src.execution.rule_engine import RuleEngine
from src.execution.schemas import (
    ApprovalDecisionRequest,
    AuditListResponse,
    ExecuteResponse,
    RiskAssessment,
    RuleResult,
    StatsResponse,
    ToolExecutionRequest,
)
from src.policies.models import Policy


class AuditLogService:
    async def record_execution(
        self,
        session: AsyncSession,
        request: ToolExecutionRequest,
        rule_results: list[RuleResult],
        risk: RiskAssessment,
        execution_time_ms: int,
    ) -> tuple[AuditLog, ApprovalRequest | None]:
        violated_policy = await self._existing_policy_code(session, risk.violated_policy)
        audit_log = AuditLog(
            agent_name=request.agent_name,
            tool_name=request.tool_name,
            action=request.action,
            decision=risk.decision,
            risk_score=risk.risk_score,
            reason=risk.reason,
            violated_policy=violated_policy,
            suggested_fix=risk.suggested_fix,
            execution_time_ms=execution_time_ms,
            request_payload=request.model_dump(mode="json"),
            response_payload={
                "risk": risk.model_dump(mode="json"),
                "rule_results": [result.model_dump(mode="json") for result in rule_results],
            },
        )
        session.add(audit_log)

        approval_request = None
        if risk.decision == Decision.CONFIRM:
            approval_request = ApprovalRequest(audit_log=audit_log)
            session.add(approval_request)

        try:
            await session.commit()
        except Exception:
            await session.rollback()
            raise

        await session.refresh(audit_log)
        if approval_request is not None:
            await session.refresh(approval_request)

        return audit_log, approval_request

    async def list_recent(
        self,
        session: AsyncSession,
        *,
        limit: int = 25,
        offset: int = 0,
        agent_name: str | None = None,
        tool_name: str | None = None,
        decision: Decision | None = None,
        min_risk_score: int | None = None,
    ) -> AuditListResponse:
        stmt = select(AuditLog).options(selectinload(AuditLog.approval_request))
        count_stmt = select(func.count()).select_from(AuditLog)

        filters = []
        if agent_name:
            filters.append(AuditLog.agent_name == agent_name)
        if tool_name:
            filters.append(AuditLog.tool_name == tool_name)
        if decision:
            filters.append(AuditLog.decision == decision)
        if min_risk_score is not None:
            filters.append(AuditLog.risk_score >= min_risk_score)

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        total = await session.scalar(count_stmt)
        result = await session.scalars(
            stmt.order_by(AuditLog.timestamp.desc())
            .limit(limit)
            .offset(offset)
        )

        return AuditListResponse(
            items=list(result.all()),
            total=total or 0,
            limit=limit,
            offset=offset,
        )

    async def get_stats(self, session: AsyncSession) -> StatsResponse:
        stmt = select(
            func.count(AuditLog.id),
            func.count(AuditLog.id).filter(AuditLog.decision == Decision.ALLOW),
            func.count(AuditLog.id).filter(AuditLog.decision == Decision.BLOCK),
            func.count(AuditLog.id).filter(AuditLog.decision == Decision.CONFIRM),
            func.avg(AuditLog.risk_score),
            func.avg(AuditLog.execution_time_ms),
            func.count(AuditLog.id).filter(AuditLog.risk_score >= 70),
        )
        row = (await session.execute(stmt)).one()

        return StatsResponse(
            total_requests=row[0] or 0,
            allowed_requests=row[1] or 0,
            blocked_requests=row[2] or 0,
            confirmation_requests=row[3] or 0,
            average_risk_score=round(float(row[4] or 0), 2),
            average_execution_time_ms=round(float(row[5] or 0), 2),
            high_risk_requests=row[6] or 0,
        )

    async def _existing_policy_code(
        self,
        session: AsyncSession,
        policy_code: str | None,
    ) -> str | None:
        if policy_code is None:
            return None

        exists = await session.scalar(
            select(Policy.policy_code).where(Policy.policy_code == policy_code)
        )
        return exists


class ApprovalService:
    async def decide(
        self,
        session: AsyncSession,
        approval_request_id: UUID,
        decision: ApprovalDecisionRequest,
    ) -> ApprovalRequest | None:
        approval_request = await session.get(ApprovalRequest, approval_request_id)
        if approval_request is None:
            return None

        approval_request.status = decision.status
        approval_request.approved_by = decision.approved_by
        approval_request.comments = decision.comments
        approval_request.approved_at = func.now()

        try:
            await session.commit()
        except Exception:
            await session.rollback()
            raise

        await session.refresh(approval_request)
        return approval_request


class PolicyService:
    async def list_active(self, session: AsyncSession) -> list[Policy]:
        result = await session.scalars(
            select(Policy)
            .where(Policy.enabled.is_(True))
            .order_by(Policy.severity.desc(), Policy.policy_code.asc())
        )
        return list(result.all())


class ExecutionService:
    def __init__(
        self,
        rule_engine: RuleEngine | None = None,
        risk_engine: RiskEngine | None = None,
        audit_log_service: AuditLogService | None = None,
    ) -> None:
        self.rule_engine = rule_engine or RuleEngine()
        self.risk_engine = risk_engine or RiskEngine()
        self.audit_log_service = audit_log_service or AuditLogService()

    async def execute(
        self,
        session: AsyncSession,
        request: ToolExecutionRequest,
    ) -> ExecuteResponse:
        started_at = perf_counter()
        rule_results = self.rule_engine.evaluate(request)
        risk = self.risk_engine.assess(rule_results, request=request)
        execution_time_ms = max(0, round((perf_counter() - started_at) * 1000))
        audit_log, approval_request = await self.audit_log_service.record_execution(
            session=session,
            request=request,
            rule_results=rule_results,
            risk=risk,
            execution_time_ms=execution_time_ms,
        )

        return ExecuteResponse(
            **risk.model_dump(),
            audit_log_id=audit_log.id,
            approval_request_id=approval_request.id if approval_request else None,
            rule_results=rule_results,
            execution_time_ms=execution_time_ms,
        )
