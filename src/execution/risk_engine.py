from src.core.enums import Decision, PolicySeverity
from src.execution.reasoning import AIReasoner, GraniteReasoner
from src.execution.schemas import RiskAssessment, RuleResult, ToolExecutionRequest

SEVERITY_WEIGHTS = {
    PolicySeverity.LOW: 10,
    PolicySeverity.MEDIUM: 25,
    PolicySeverity.HIGH: 45,
    PolicySeverity.CRITICAL: 70,
}


class RiskEngine:
    def __init__(self, reasoner: AIReasoner | None = None) -> None:
        self.reasoner = reasoner or GraniteReasoner()

    def assess(
        self,
        rule_results: list[RuleResult],
        request: ToolExecutionRequest | None = None,
    ) -> RiskAssessment:
        failed_rules = [result for result in rule_results if not result.passed]
        risk_score = min(
            100,
            sum(SEVERITY_WEIGHTS[result.severity] for result in failed_rules),
        )
        decision = self._decision_for_score(risk_score)

        # Fallback request object if none provided
        req = request or ToolExecutionRequest(
            agent_name="unknown",
            tool_name="unknown",
            action="unknown",
        )

        reasoning = self.reasoner.explain(req, failed_rules)

        return RiskAssessment(
            risk_score=risk_score,
            decision=decision,
            reason=reasoning.explanation,
            violated_policy=reasoning.violated_policy,
            suggested_fix=reasoning.suggested_fix,
            confidence_score=reasoning.confidence_score,
        )

    @staticmethod
    def _decision_for_score(risk_score: int) -> Decision:
        if risk_score <= 30:
            return Decision.ALLOW
        if risk_score <= 70:
            return Decision.CONFIRM
        return Decision.BLOCK
