from src.core.enums import Decision
from src.execution.risk_engine import RiskEngine
from src.execution.rule_engine import RuleEngine
from src.execution.schemas import ToolExecutionRequest


def test_rule_engine_collects_all_rule_results() -> None:
    request = ToolExecutionRequest(
        agent_name="research-agent",
        tool_name="email",
        action="send_sensitive_email",
        parameters={"token": "raw-secret"},
        requested_scope="external_email",
        allowed_scopes=["calendar"],
        estimated_cost_usd=25,
        is_irreversible=True,
        recent_requests_count=150,
    )

    results = RuleEngine().evaluate(request)

    assert len(results) == 5
    assert all(not result.passed for result in results)
    assert {result.policy_code for result in results} == {
        "SCOPE_BOUNDARY",
        "PARAMETER_SAFETY",
        "RATE_LIMIT",
        "COST_LIMIT",
        "IRREVERSIBLE_ACTION",
    }


def test_risk_engine_allows_low_risk_requests() -> None:
    request = ToolExecutionRequest(
        agent_name="research-agent",
        tool_name="calendar",
        action="read_events",
        requested_scope="calendar",
        allowed_scopes=["calendar"],
    )
    rule_results = RuleEngine().evaluate(request)

    risk = RiskEngine().assess(rule_results)

    assert risk.risk_score == 0
    assert risk.decision == Decision.ALLOW
    assert risk.violated_policy is None


def test_risk_engine_blocks_combined_high_risk_failures() -> None:
    request = ToolExecutionRequest(
        agent_name="ops-agent",
        tool_name="payment_processor",
        action="refund_batch",
        estimated_cost_usd=50,
        is_irreversible=True,
    )
    rule_results = RuleEngine().evaluate(request)

    risk = RiskEngine().assess(rule_results)

    assert risk.risk_score == 90
    assert risk.decision == Decision.BLOCK
    assert risk.violated_policy == "COST_LIMIT"

