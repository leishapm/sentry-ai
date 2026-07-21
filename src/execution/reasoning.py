from typing import Protocol

from src.execution.schemas import RuleResult


class DecisionReasoner(Protocol):
    def explain(self, failed_rules: list[RuleResult]) -> tuple[str, str | None]:
        """Return a decision reason and suggested fix."""


class PlaceholderDecisionReasoner:
    def explain(self, failed_rules: list[RuleResult]) -> tuple[str, str | None]:
        if not failed_rules:
            return "All placeholder rule checks passed.", None

        failed_rule_names = ", ".join(rule.rule for rule in failed_rules)
        first_fix = next(
            (rule.suggested_fix for rule in failed_rules if rule.suggested_fix),
            "Review the failed policy checks before executing the tool request.",
        )
        return f"Placeholder risk assessment found failed checks: {failed_rule_names}.", first_fix

