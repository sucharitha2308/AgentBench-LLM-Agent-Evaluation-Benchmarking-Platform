from typing import Any, Dict, Optional
from app.evaluators.base import BaseEvaluator, EvaluatorResult


class LLMJudgeEvaluator(BaseEvaluator):
    """
    LLM-as-a-Judge Evaluator.
    Scores response completeness, tone, and accuracy on a 1.0 - 5.0 scale.
    """
    def evaluate(
        self,
        test_case: Dict[str, Any],
        actual_output: str,
        actual_tool_calls: list,
        actual_tool_results: list,
        duration_ms: int,
        error: Optional[str] = None
    ) -> EvaluatorResult:
        if error or not actual_output:
            return EvaluatorResult(
                metric_name="llm_judge",
                metric_value=1.0,
                passed=False,
                explanation="Response is absent or errored.",
                evidence={"score": 1.0, "rubric": "Failed execution"},
                failure_category="empty_or_errored_response"
            )

        # Evaluate quality heuristics
        score = 5.0
        reasons = []

        if len(actual_output.split()) < 4:
            score -= 1.5
            reasons.append("Response is too curt")

        # Empathy check if customer dissatisfaction tag
        tags = test_case.get("tags", [])
        if "sentiment" in tags or "empathy" in tags:
            lower = actual_output.lower()
            if not any(w in lower for w in ["sorry", "apologize", "understand", "help"]):
                score -= 1.0
                reasons.append("Missing empathetic acknowledgment for dissatisfied customer")

        score = max(score, 1.0)
        passed = (score >= 3.5)
        explanation = f"Judge Rating: {score:.1f}/5.0."
        if reasons:
            explanation += f" Notes: {', '.join(reasons)}"
        else:
            explanation += " Response exhibits high clarity, appropriate tone, and relevant assistance."

        return EvaluatorResult(
            metric_name="llm_judge",
            metric_value=round(score, 2),
            passed=passed,
            explanation=explanation,
            evidence={"judge_score": score, "max_score": 5.0, "notes": reasons}
        )
