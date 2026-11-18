from typing import Any, Dict, Optional
from app.evaluators.base import BaseEvaluator, EvaluatorResult


class PerformanceEvaluator(BaseEvaluator):
    """
    Evaluates execution latency against maximum allowed latency SLA.
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
        max_latency = test_case.get("max_allowed_latency_ms", 3500)
        passed = (duration_ms <= max_latency)
        
        explanation = f"Execution finished in {duration_ms}ms (SLA threshold: {max_latency}ms)."
        if not passed:
            explanation += f" Latency exceeded SLA by {duration_ms - max_latency}ms."

        return EvaluatorResult(
            metric_name="performance",
            metric_value=float(duration_ms),
            passed=passed,
            explanation=explanation,
            evidence={
                "duration_ms": duration_ms,
                "max_allowed_latency_ms": max_latency,
                "latency_slack_ms": max_latency - duration_ms
            },
            failure_category="latency_sla_exceeded" if not passed else None
        )
