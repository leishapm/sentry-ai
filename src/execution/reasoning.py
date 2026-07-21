from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from src.core.enums import PolicySeverity
from src.execution.schemas import RuleResult, ToolExecutionRequest


class ReasoningOutput(BaseModel):
    model_config = ConfigDict(frozen=True)

    explanation: str = Field(description="Detailed explanation of the risk assessment and decision.")
    violated_policy: str | None = Field(default=None, description="Primary policy code violated, if any.")
    suggested_fix: str | None = Field(default=None, description="Actionable recommendation to fix or mitigate the issue.")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence level of the reasoning model (0.0 to 1.0).")


class AIReasoner(Protocol):
    """Clean interface for AI reasoning services (e.g. IBM Granite, Rule-based, etc.)."""

    def explain(
        self,
        request: ToolExecutionRequest,
        failed_rules: list[RuleResult],
    ) -> ReasoningOutput:
        """Analyze tool request and failed rules to produce structured reasoning output."""
        ...


# Alias for backward compatibility
PolicyReasoner = AIReasoner


class GraniteReasoner:
    """IBM Granite AI Reasoning model implementation (placeholder with integration hook).

    Ready to be plugged into the real IBM Granite API / watsonx.ai SDK.
    """

    def __init__(self, api_key: str | None = None, model_id: str = "ibm/granite-3-8b-instruct") -> None:
        self.api_key = api_key
        self.model_id = model_id

    def explain(
        self,
        request: ToolExecutionRequest,
        failed_rules: list[RuleResult],
    ) -> ReasoningOutput:
        if not failed_rules:
            return ReasoningOutput(
                explanation=(
                    f"Granite Reasoning Engine ({self.model_id}): Tool execution request for '{request.tool_name}' "
                    f"acting on '{request.action}' by agent '{request.agent_name}' satisfies all active safety policies."
                ),
                violated_policy=None,
                suggested_fix=None,
                confidence_score=0.99,
            )

        primary_failed = failed_rules[0]
        failed_rule_names = ", ".join(rule.rule for rule in failed_rules)
        severities = [rule.severity for rule in failed_rules]

        # Calculate confidence score based on severity consistency
        confidence_score = 0.95
        if PolicySeverity.CRITICAL in severities:
            confidence_score = 0.98
        elif PolicySeverity.HIGH in severities:
            confidence_score = 0.92
        elif PolicySeverity.MEDIUM in severities:
            confidence_score = 0.88

        explanation = (
            f"Granite Reasoning Engine ({self.model_id}) detected policy violation(s) [{failed_rule_names}] "
            f"for agent '{request.agent_name}' calling tool '{request.tool_name}' (action: '{request.action}'). "
            f"Primary concern: {primary_failed.reason}"
        )

        fix = primary_failed.suggested_fix or "Review policy violations and request human approval if required."

        return ReasoningOutput(
            explanation=explanation,
            violated_policy=primary_failed.policy_code,
            suggested_fix=fix,
            confidence_score=confidence_score,
        )


class RuleBasedReasoner:
    """Fallback rule-based decision reasoner."""

    def explain(
        self,
        request: ToolExecutionRequest,
        failed_rules: list[RuleResult],
    ) -> ReasoningOutput:
        if not failed_rules:
            return ReasoningOutput(
                explanation="All policy checks passed successfully.",
                violated_policy=None,
                suggested_fix=None,
                confidence_score=1.0,
            )

        failed_names = ", ".join(rule.rule for rule in failed_rules)
        first_fix = next(
            (rule.suggested_fix for rule in failed_rules if rule.suggested_fix),
            "Review failed policy checks before executing the tool request.",
        )
        return ReasoningOutput(
            explanation=f"Rule assessment failed checks: {failed_names}.",
            violated_policy=failed_rules[0].policy_code,
            suggested_fix=first_fix,
            confidence_score=0.90,
        )


# Backward compatibility alias
PlaceholderDecisionReasoner = GraniteReasoner
