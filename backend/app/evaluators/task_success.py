from typing import Any, Dict, Optional
from app.evaluators.base import BaseEvaluator, EvaluatorResult


class TaskSuccessEvaluator(BaseEvaluator):
    """
    Evaluates whether the agent successfully accomplished the end goal of the test case.
    Considers tool calls, outputs, errors, and requirements.
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
            return EvaluatorResult(
                metric_name="task_success",
                metric_value=0.0,
                passed=False,
                explanation=f"Task failed due to runtime execution error: {error}",
                evidence={"error": error},
                failure_category="runtime_error"
            )

        expected_tools = test_case.get("expected_tool_calls", [])
        expected_output = test_case.get("expected_output", {}) or {}
        criteria = test_case.get("evaluation_criteria", {}) or {}

        # 1. Tool execution verification
        if expected_tools and criteria.get("require_tool_selection", True):
            actual_tool_names = [tc.get("tool_name") for tc in actual_tool_calls]
            expected_tool_names = [etc.get("tool_name") for etc in expected_tools]
            missing = [t for t in expected_tool_names if t not in actual_tool_names]
            if missing:
                return EvaluatorResult(
                    metric_name="task_success",
                    metric_value=0.0,
                    passed=False,
                    explanation=f"Required tools were not executed: {', '.join(missing)}",
                    evidence={"missing_tools": missing, "actual_tools": actual_tool_names},
                    failure_category="tool_call_missing"
                )

        # 2. Output keywords check
        keywords = expected_output.get("contains_keywords", [])
        if keywords:
            output_lower = actual_output.lower()
            found = [k for k in keywords if k.lower() in output_lower]
            # Require at least one significant keyword match
            if not found:
                return EvaluatorResult(
                    metric_name="task_success",
                    metric_value=0.0,
                    passed=False,
                    explanation=f"Response output missed all expected keywords: {keywords}",
                    evidence={"expected_keywords": keywords, "output_snippet": actual_output[:200]},
                    failure_category="semantic_mismatch"
                )

        return EvaluatorResult(
            metric_name="task_success",
            metric_value=1.0,
            passed=True,
            explanation="Task completed successfully meeting all expected criteria and tool expectations.",
            evidence={
                "tools_executed": len(actual_tool_calls),
                "duration_ms": duration_ms
            }
        )
