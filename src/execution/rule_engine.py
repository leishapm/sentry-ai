from collections.abc import Callable, Sequence

from src.core.enums import PolicySeverity
from src.execution.sanitization import contains_credential
from src.execution.schemas import RuleResult, ToolExecutionRequest

Rule = Callable[[ToolExecutionRequest], RuleResult]
NON_DISABLEABLE_POLICY_CODES = frozenset({"PARAMETER_SAFETY"})

def check_scope(request: ToolExecutionRequest) -> RuleResult:
    if request.requested_scope is not None and (
        not request.allowed_scopes or request.requested_scope not in request.allowed_scopes
    ):
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
    credential_found = any(
        contains_credential(value)
        for value in (request.parameters, request.context, request.action)
    )
    if credential_found:
        return RuleResult(
            rule="Parameter Check",
            policy_code="PARAMETER_SAFETY",
            passed=False,
            severity=PolicySeverity.CRITICAL,
            reason="Request contains credential-like fields and is blocked to prevent secret disclosure.",
            suggested_fix="Remove credentials from the tool request and use a server-side secret reference.",
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
    # `user_confirmed` is supplied by the caller and cannot establish that a
    # human actually approved the action. Irreversible actions must go through
    # the server-side approval workflow.
    if request.is_irreversible:
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

    def evaluate(
        self,
        request: ToolExecutionRequest,
        disabled_policy_codes: set[str] | frozenset[str] = frozenset(),
    ) -> list[RuleResult]:
        results = [rule(request) for rule in self.rules]
        return [
            result.model_copy(
                update={
                    "passed": True,
                    "reason": "Policy is disabled by an administrator.",
                    "suggested_fix": None,
                }
            )
            if result.policy_code in disabled_policy_codes
            and result.policy_code not in NON_DISABLEABLE_POLICY_CODES
            else result
            for result in results
        ]
