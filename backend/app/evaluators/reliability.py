from typing import Any, Dict, Optional
from app.evaluators.base import BaseEvaluator, EvaluatorResult


class ReliabilityEvaluator(BaseEvaluator):
    """
    Evaluates execution stability: catches provider exceptions, tool execution crashes,
    timeouts, or malformed responses.
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
        if error:
            is_timeout = "timeout" in error.lower()
            return EvaluatorResult(
                metric_name="reliability",
                metric_value=0.0,
                passed=False,
                explanation=f"Execution error encountered: {error}",
                evidence={"error": error, "is_timeout": is_timeout},
                failure_category="timeout_error" if is_timeout else "provider_error"
            )

        # Check for tool execution errors
        tool_failures = []
        for tr in actual_tool_results:
            res = tr.get("result", {})
            if isinstance(res, dict) and not res.get("success", True) and "not found" not in res.get("error", "").lower():
                tool_failures.append({"tool": tr.get("tool_name"), "error": res.get("error")})

        if tool_failures:
            return EvaluatorResult(
                metric_name="reliability",
                metric_value=0.5,
                passed=False,
                explanation=f"Tool execution failed for: {tool_failures}",
                evidence={"tool_failures": tool_failures},
                failure_category="tool_execution_crash"
            )

        return EvaluatorResult(
            metric_name="reliability",
            metric_value=1.0,
            passed=True,
            explanation="Execution completed with zero provider crashes or tool infrastructure errors.",
            evidence={"tool_count": len(actual_tool_calls)}
        )
