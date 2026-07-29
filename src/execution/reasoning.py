import json
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from src.core.config import settings
from src.core.enums import PolicySeverity
from src.core.logging import get_logger
from src.execution.schemas import RuleResult, ToolExecutionRequest

logger = get_logger(__name__)

GRANITE_SYSTEM_PROMPT = """You are SENTRY's AI reasoning layer. Rule-based policy checks have \
already run against an AI agent's tool-call request and their results are given to you below. \
Your job is to produce a clear, human-readable explanation grounded in those results - you do \
NOT decide ALLOW/BLOCK/CONFIRM yourself, that is computed separately from rule severity scores.

Respond with ONLY a JSON object, no other text, matching exactly this shape:
{
  "explanation": "1-2 sentences explaining the assessment, grounded in the failed rule(s) below",
  "violated_policy": "policy_code of the primary/most severe violation, or null if none failed",
  "suggested_fix": "actionable recommendation, or null if none failed",
  "confidence_score": a number between 0.0 and 1.0
}"""


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
    """IBM Granite AI Reasoning model implementation.

    Calls watsonx.ai/Granite for the explanation when WATSONX_API_KEY and
    WATSONX_PROJECT_ID are configured. Falls back to a deterministic templated
    explanation - the original placeholder behaviour - when credentials aren't
    set, or if the live call fails for any reason, so the reasoning layer never
    blocks a decision on an external API being unavailable.
    """

    def __init__(self, api_key: str | None = None, model_id: str | None = None) -> None:
        self.api_key = api_key or settings.watsonx_api_key
        self.model_id = model_id or settings.watsonx_model_id
        self._client = None
        if self.api_key and settings.watsonx_project_id:
            try:
                self._client = self._build_client()
            except Exception:
                # ibm-watsonx-ai eagerly validates the project/credentials by
                # fetching model specs at construction time, so a misconfigured
                # project (no WML instance associated, bad key, network issue)
                # would otherwise crash every single request that instantiates
                # a GraniteReasoner - not just this one call. Fail safe instead.
                logger.exception("Failed to initialize watsonx client; falling back to templated explanations")

    def _build_client(self):
        from ibm_watsonx_ai import Credentials
        from ibm_watsonx_ai.foundation_models import ModelInference

        return ModelInference(
            model_id=self.model_id,
            credentials=Credentials(url=settings.watsonx_url, api_key=self.api_key),
            project_id=settings.watsonx_project_id,
            params={"temperature": 0, "max_new_tokens": 300},
        )

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

        if self._client is not None:
            try:
                return self._explain_with_granite(request, failed_rules)
            except Exception:
                logger.exception("watsonx call failed; falling back to templated explanation")

        return self._placeholder_explain(request, failed_rules)

    def _explain_with_granite(
        self,
        request: ToolExecutionRequest,
        failed_rules: list[RuleResult],
    ) -> ReasoningOutput:
        rules_summary = "\n".join(
            f"- rule={rule.rule} policy_code={rule.policy_code} severity={rule.severity.value} "
            f"reason={rule.reason!r} suggested_fix={rule.suggested_fix!r}"
            for rule in failed_rules
        )
        user_content = (
            f"Agent: {request.agent_name}\n"
            f"Tool: {request.tool_name}\n"
            f"Action: {request.action}\n"
            f"Parameters: {json.dumps(request.parameters)}\n\n"
            f"Failed policy checks:\n{rules_summary}"
        )
        response = self._client.chat(
            messages=[
                {"role": "system", "content": GRANITE_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ]
        )
        parsed = self._parse_response(response["choices"][0]["message"]["content"])
        return ReasoningOutput(
            explanation=parsed["explanation"],
            violated_policy=parsed.get("violated_policy"),
            suggested_fix=parsed.get("suggested_fix"),
            confidence_score=float(parsed.get("confidence_score", 0.9)),
        )

    @staticmethod
    def _parse_response(raw: str) -> dict:
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`")
            text = text.split("\n", 1)[1] if "\n" in text else text
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(f"No JSON object found in Granite response: {raw!r}")
        return json.loads(text[start : end + 1])

    @staticmethod
    def _placeholder_explain(
        request: ToolExecutionRequest,
        failed_rules: list[RuleResult],
    ) -> ReasoningOutput:
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
            f"Granite Reasoning Engine detected policy violation(s) [{failed_rule_names}] "
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
