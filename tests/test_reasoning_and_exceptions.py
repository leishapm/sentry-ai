import pytest
from fastapi import status
from fastapi.testclient import TestClient

from src.core.config import settings
from src.core.enums import Decision, PolicySeverity
from src.core.exceptions import EntityNotFoundException, InvalidOperationException
from src.execution.reasoning import GraniteReasoner, ReasoningOutput, RuleBasedReasoner
from src.execution.risk_engine import RiskEngine
from src.execution.rule_engine import RuleEngine
from src.execution.schemas import RuleResult, ToolExecutionRequest
from src.main import app


@pytest.fixture(autouse=True)
def _force_offline_granite(monkeypatch: pytest.MonkeyPatch) -> None:
    """These tests assert on GraniteReasoner's deterministic placeholder
    output, not real Granite output. Without this, a developer with a local
    .env containing real watsonx credentials would have these tests silently
    make real network calls to IBM Cloud and fail on non-deterministic LLM
    text/confidence scores instead of testing the fallback logic."""
    monkeypatch.setattr(settings, "watsonx_api_key", None)
    monkeypatch.setattr(settings, "watsonx_project_id", None)


def test_granite_reasoner_pass_output() -> None:
    reasoner = GraniteReasoner()
    request = ToolExecutionRequest(
        agent_name="data-agent",
        tool_name="database",
        action="read_table",
    )
    output = reasoner.explain(request, [])

    assert isinstance(output, ReasoningOutput)
    assert "Granite Reasoning Engine" in output.explanation
    assert output.violated_policy is None
    assert output.suggested_fix is None
    assert output.confidence_score == 0.99


def test_granite_reasoner_failed_rule_output() -> None:
    reasoner = GraniteReasoner()
    request = ToolExecutionRequest(
        agent_name="ops-agent",
        tool_name="aws_cli",
        action="terminate_instance",
    )
    failed_rule = RuleResult(
        rule="Irreversibility Check",
        policy_code="IRREVERSIBLE_ACTION",
        passed=False,
        severity=PolicySeverity.CRITICAL,
        reason="Action is irreversible and unconfirmed.",
        suggested_fix="Obtain human confirmation.",
    )
    output = reasoner.explain(request, [failed_rule])

    assert output.violated_policy == "IRREVERSIBLE_ACTION"
    assert output.suggested_fix == "Obtain human confirmation."
    assert output.confidence_score == 0.98
    assert "detected policy violation(s)" in output.explanation


def test_risk_engine_with_granite_reasoner() -> None:
    request = ToolExecutionRequest(
        agent_name="finance-agent",
        tool_name="stripe",
        action="charge",
        estimated_cost_usd=100.0,
    )
    rule_results = RuleEngine().evaluate(request)
    risk_engine = RiskEngine(reasoner=GraniteReasoner())
    assessment = risk_engine.assess(rule_results, request=request)

    assert assessment.decision == Decision.CONFIRM
    assert assessment.risk_score == 45
    assert assessment.violated_policy == "COST_LIMIT"
    assert assessment.confidence_score > 0.0


def test_custom_exception_handlers() -> None:
    client = TestClient(app)

    # Test invalid JSON validation error (422)
    response = client.post("/execute", json={"invalid": "data"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
