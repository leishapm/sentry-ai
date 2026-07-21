from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.execution.reasoning import AIReasoner, GraniteReasoner
from src.execution.services import (
    ApprovalService,
    AuditLogService,
    ExecutionService,
    PolicyService,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_session():
        yield session


def get_reasoner() -> AIReasoner:
    return GraniteReasoner()


def get_execution_service() -> ExecutionService:
    return ExecutionService()


def get_audit_log_service() -> AuditLogService:
    return AuditLogService()


def get_approval_service() -> ApprovalService:
    return ApprovalService()


def get_policy_service() -> PolicyService:
    return PolicyService()
