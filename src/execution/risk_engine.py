from src.core.enums import Decision, PolicySeverity
from src.execution.reasoning import DecisionReasoner, PlaceholderDecisionReasoner
from src.execution.schemas import RiskAssessment, RuleResult

SEVERITY_WEIGHTS = {
    PolicySeverity.LOW: 10,
    PolicySeverity.MEDIUM: 25,
    PolicySeverity.HIGH: 45,
    PolicySeverity.CRITICAL: 70,
}


class RiskEngine:
    def __init__(self, reasoner: DecisionReasoner | None = None) -> None:
        self.reasoner = reasoner or PlaceholderDecisionReasoner()

    def assess(self, rule_results: list[RuleResult]) -> RiskAssessment:
        failed_rules = [result for result in rule_results if not result.passed]
        risk_score = min(
            100,
            sum(SEVERITY_WEIGHTS[result.severity] for result in failed_rules),
        )
        decision = self._decision_for_score(risk_score)
        reason, suggested_fix = self.reasoner.explain(failed_rules)

        return RiskAssessment(
            risk_score=risk_score,
            decision=decision,
            reason=reason,
            violated_policy=failed_rules[0].policy_code if failed_rules else None,
            suggested_fix=suggested_fix,
        )

    @staticmethod
    def _decision_for_score(risk_score: int) -> Decision:
        if risk_score <= 30:
            return Decision.ALLOW
        if risk_score <= 70:
            return Decision.CONFIRM
        return Decision.BLOCK

