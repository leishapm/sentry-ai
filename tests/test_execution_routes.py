from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, MagicMock

from src.core.enums import ApprovalStatus, Decision, PolicySeverity
from src.db.session import get_session
from src.execution.router import (
    get_approval_service,
    get_audit_log_service,
    get_execution_service,
    get_policy_service,
)
from src.execution.schemas import (
    ApprovalDecisionRequest,
    AuditListResponse,
    ExecuteResponse,
    RuleResult,
    StatsResponse,
)
from src.main import app


class FakeExecutionService:
    async def execute(self, session: object, request: object) -> ExecuteResponse:
        return ExecuteResponse(
            audit_log_id=UUID("00000000-0000-0000-0000-000000000001"),
            approval_request_id=None,
            risk_score=0,
            decision=Decision.ALLOW,
            reason="All placeholder rule checks passed.",
            violated_policy=None,
            suggested_fix=None,
            confidence_score=0.99,
            execution_time_ms=1,
            rule_results=[
                RuleResult(
                    rule="Scope Check",
                    policy_code="SCOPE_BOUNDARY",
                    passed=True,
                    severity=PolicySeverity.HIGH,
                    reason="Requested scope is permitted.",
                )
            ],
        )


class FakeAuditLogService:
    async def list_recent(
        self,
        session: object,
        *,
        limit: int,
        offset: int,
        **kwargs: object,
    ) -> AuditListResponse:
        return AuditListResponse(items=[], total=0, limit=limit, offset=offset)

    async def get_stats(self, session: object) -> StatsResponse:
        return StatsResponse(
            total_requests=10,
            allowed_requests=5,
            blocked_requests=2,
            confirmation_requests=3,
            average_risk_score=42.5,
            average_execution_time_ms=12.5,
            high_risk_requests=2,
        )


class FakeApprovalService:
    async def decide(
        self,
        session: object,
        approval_request_id: UUID,
        decision: ApprovalDecisionRequest,
    ) -> SimpleNamespace:
        return SimpleNamespace(
            id=approval_request_id,
            audit_log_id=uuid4(),
            status=decision.status,
            approved_by=decision.approved_by,
            approved_at=datetime.now(UTC),
            comments=decision.comments,
        )


class FakePolicyService:
    async def list_active(self, session: object) -> list[SimpleNamespace]:
        now = datetime.now(UTC)
        return [
            SimpleNamespace(
                id=uuid4(),
                policy_code="SCOPE_BOUNDARY",
                name="Scope Boundary",
                description="Prevents out-of-scope actions.",
                severity=PolicySeverity.HIGH,
                enabled=True,
                created_at=now,
                updated_at=now,
            )
        ]


async def fake_session() -> object:
    mock = AsyncMock()
    mock.execute = AsyncMock(return_value=MagicMock())
    yield mock


@pytest.fixture(autouse=True)
def override_dependencies() -> None:
    app.dependency_overrides[get_session] = fake_session
    app.dependency_overrides[get_execution_service] = lambda: FakeExecutionService()
    app.dependency_overrides[get_audit_log_service] = lambda: FakeAuditLogService()
    app.dependency_overrides[get_approval_service] = lambda: FakeApprovalService()
    app.dependency_overrides[get_policy_service] = lambda: FakePolicyService()
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_execute_endpoint_returns_decision() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/execute",
            json={
                "agent_name": "research-agent",
                "tool_name": "calendar",
                "action": "read_events",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "ALLOW"
    assert body["audit_log_id"] == "00000000-0000-0000-0000-000000000001"
    assert body["confidence_score"] == 0.99


@pytest.mark.asyncio
async def test_audit_endpoint_supports_pagination() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/audit?limit=10&offset=5")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "limit": 10, "offset": 5}


@pytest.mark.asyncio
async def test_stats_endpoint_returns_dashboard_counts() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/stats")

    assert response.status_code == 200
    assert response.json()["average_risk_score"] == 42.5
    assert response.json()["high_risk_requests"] == 2


@pytest.mark.asyncio
async def test_approve_endpoint_updates_terminal_status() -> None:
    approval_request_id = uuid4()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            f"/approve/{approval_request_id}",
            json={
                "status": "APPROVED",
                "approved_by": "human-reviewer",
                "comments": "Looks acceptable.",
            },
        )

    assert response.status_code == 200
    assert response.json()["id"] == str(approval_request_id)
    assert response.json()["status"] == ApprovalStatus.APPROVED


@pytest.mark.asyncio
async def test_policies_endpoint_returns_active_policies() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/policies")

    assert response.status_code == 200
    assert response.json()[0]["policy_code"] == "SCOPE_BOUNDARY"
