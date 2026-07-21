from collections.abc import Callable, Sequence

from src.core.enums import PolicySeverity
from src.execution.schemas import RuleResult, ToolExecutionRequest

Rule = Callable[[ToolExecutionRequest], RuleResult]

SENSITIVE_PARAMETER_NAMES = frozenset(
    {
        "api_key",
        "authorization",
        "password",
        "private_key",
        "secret",
        "token",
    }
)


def check_scope(request: ToolExecutionRequest) -> RuleResult:
    if request.allowed_scopes and request.requested_scope not in request.allowed_scopes:
        return RuleResult(
            rule="Scope Check",
            policy_code="SCOPE_BOUNDARY",
            passed=False,
            severity=PolicySeverity.HIGH,
            reason="Agent attempted an action outside its permitted scope.",
            suggested_fix="Restrict the request to an allowed scope or request human approval.",
        )

    return RuleResult(
        rule="Scope Check",
        policy_code="SCOPE_BOUNDARY",
        passed=True,
        severity=PolicySeverity.HIGH,
        reason="Requested scope is permitted.",
    )


def check_parameters(request: ToolExecutionRequest) -> RuleResult:
    sensitive_keys = SENSITIVE_PARAMETER_NAMES.intersection(
        key.lower() for key in request.parameters
    )
    if sensitive_keys:
        return RuleResult(
            rule="Parameter Check",
            policy_code="PARAMETER_SAFETY",
            passed=False,
            severity=PolicySeverity.MEDIUM,
            reason="Request parameters include sensitive-looking fields.",
            suggested_fix="Redact secrets before sending tool requests through SENTRY.",
        )

    return RuleResult(
        rule="Parameter Check",
        policy_code="PARAMETER_SAFETY",
        passed=True,
        severity=PolicySeverity.MEDIUM,
        reason="Request parameters passed placeholder validation.",
    )


def check_rate_limit(request: ToolExecutionRequest) -> RuleResult:
    if request.recent_requests_count > 100:
        return RuleResult(
            rule="Rate Limit Check",
            policy_code="RATE_LIMIT",
            passed=False,
            severity=PolicySeverity.MEDIUM,
            reason="Agent has exceeded the placeholder request volume threshold.",
            suggested_fix="Retry later or reduce tool call frequency.",
        )

    return RuleResult(
        rule="Rate Limit Check",
        policy_code="RATE_LIMIT",
        passed=True,
        severity=PolicySeverity.MEDIUM,
        reason="Agent is within the placeholder request volume threshold.",
    )


def check_cost(request: ToolExecutionRequest) -> RuleResult:
    if request.estimated_cost_usd is not None and request.estimated_cost_usd > 10:
        return RuleResult(
            rule="Cost Check",
            policy_code="COST_LIMIT",
            passed=False,
            severity=PolicySeverity.HIGH,
            reason="Estimated tool execution cost exceeds the placeholder budget.",
            suggested_fix="Lower the requested cost or request human approval.",
        )

    return RuleResult(
        rule="Cost Check",
        policy_code="COST_LIMIT",
        passed=True,
        severity=PolicySeverity.HIGH,
        reason="Estimated cost is within the placeholder budget.",
    )


def check_irreversible(request: ToolExecutionRequest) -> RuleResult:
    if request.is_irreversible and not request.user_confirmed:
        return RuleResult(
            rule="Irreversibility Check",
            policy_code="IRREVERSIBLE_ACTION",
            passed=False,
            severity=PolicySeverity.HIGH,
            reason="Request may perform an irreversible action without prior confirmation.",
            suggested_fix="Ask a human to confirm before executing irreversible actions.",
        )

    return RuleResult(
        rule="Irreversibility Check",
        policy_code="IRREVERSIBLE_ACTION",
        passed=True,
        severity=PolicySeverity.HIGH,
        reason="Irreversibility requirements passed placeholder validation.",
    )


class RuleEngine:
    def __init__(self, rules: Sequence[Rule] | None = None) -> None:
        self.rules = tuple(
            rules
            or (
                check_scope,
                check_parameters,
                check_rate_limit,
                check_cost,
                check_irreversible,
            )
        )

    def evaluate(self, request: ToolExecutionRequest) -> list[RuleResult]:
        return [rule(request) for rule in self.rules]

