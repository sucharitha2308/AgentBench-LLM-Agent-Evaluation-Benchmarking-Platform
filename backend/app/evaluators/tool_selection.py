from typing import Any, Dict, List, Optional
from app.evaluators.base import BaseEvaluator, EvaluatorResult


class ToolSelectionEvaluator(BaseEvaluator):
    """
    Evaluates precision, recall, and F1 score of tool selection.
    Detects missing, unnecessary, correct, and incorrect tool calls.
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
        expected_tools: List[Dict[str, Any]] = test_case.get("expected_tool_calls", [])
        expected_names = [t.get("tool_name") for t in expected_tools if t.get("tool_name")]
        actual_names = [t.get("tool_name") for t in actual_tool_calls if t.get("tool_name")]

        # Case 1: Both expected and actual are empty (no tool needed and none called)
        if not expected_names and not actual_names:
            return EvaluatorResult(
                metric_name="tool_selection",
                metric_value=1.0,
                passed=True,
                explanation="Correctly refrained from invoking any tool.",
                evidence={"precision": 1.0, "recall": 1.0, "f1": 1.0}
            )

        # Case 2: Expected no tools, but some were called (hallucinated / unnecessary tools)
        if not expected_names and actual_names:
            return EvaluatorResult(
                metric_name="tool_selection",
                metric_value=0.0,
                passed=False,
                explanation=f"Unnecessary tool calls detected: {', '.join(actual_names)}",
                evidence={"unnecessary_tools": actual_names, "precision": 0.0, "recall": 0.0, "f1": 0.0},
                failure_category="unnecessary_tool_call"
            )

        # Case 3: Expected tools, but none called
        if expected_names and not actual_names:
            return EvaluatorResult(
                metric_name="tool_selection",
                metric_value=0.0,
                passed=False,
                explanation=f"Missing expected tool calls: {', '.join(expected_names)}",
                evidence={"missing_tools": expected_names, "precision": 0.0, "recall": 0.0, "f1": 0.0},
                failure_category="missing_tool_call"
            )

        # Case 4: General precision/recall/F1 calculation
        true_positives = 0
        actual_copy = list(actual_names)
        for expected in expected_names:
            if expected in actual_copy:
                true_positives += 1
                actual_copy.remove(expected)

        precision = true_positives / len(actual_names) if actual_names else 0.0
        recall = true_positives / len(expected_names) if expected_names else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        missing = [t for t in expected_names if t not in actual_names]
        unnecessary = [t for t in actual_names if t not in expected_names]

        passed = (f1 >= 0.8)
        explanation = (
            f"Tool selection F1 score: {f1:.2f} (Precision: {precision:.2f}, Recall: {recall:.2f})"
        )
        if missing:
            explanation += f" | Missing: {', '.join(missing)}"
        if unnecessary:
            explanation += f" | Unnecessary: {', '.join(unnecessary)}"

        return EvaluatorResult(
            metric_name="tool_selection",
            metric_value=round(f1, 4),
            passed=passed,
            explanation=explanation,
            evidence={
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": round(f1, 4),
                "expected": expected_names,
                "actual": actual_names,
                "missing": missing,
                "unnecessary": unnecessary
            },
            failure_category="tool_selection_mismatch" if not passed else None
        )
