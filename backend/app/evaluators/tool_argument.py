from typing import Any, Dict, List, Optional
from app.evaluators.base import BaseEvaluator, EvaluatorResult


def normalize_value(val: Any) -> Any:
    if isinstance(val, str):
        return val.strip().lower()
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, dict):
        return {k.lower(): normalize_value(v) for k, v in val.items()}
    if isinstance(val, list):
        return [normalize_value(x) for x in val]
    return val


def values_match(expected: Any, actual: Any) -> bool:
    norm_exp = normalize_value(expected)
    norm_act = normalize_value(actual)
    
    if norm_exp == norm_act:
        return True
    
    # If string, check partial containment (e.g. for search queries)
    if isinstance(norm_exp, str) and isinstance(norm_act, str):
        if norm_exp in norm_act or norm_act in norm_exp:
            return True
            
    return False


class ToolArgumentEvaluator(BaseEvaluator):
    """
    Evaluates accuracy and conformity of arguments passed to tool calls.
    Performs normalized, schema-aware comparison of parameters.
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
        
        # If no expected tool calls, argument evaluation is not applicable / 1.0
        if not expected_tools:
            return EvaluatorResult(
                metric_name="tool_argument",
                metric_value=1.0,
                passed=True,
                explanation="No tool arguments required for this test case.",
                evidence={"total_arguments_checked": 0}
            )

        total_args = 0
        matched_args = 0
        mismatches = []

        for expected in expected_tools:
            tool_name = expected.get("tool_name")
            expected_args = expected.get("arguments", {})
            
            # Find corresponding actual tool call
            matching_actual = next(
                (at for at in actual_tool_calls if at.get("tool_name") == tool_name),
                None
            )

            if not matching_actual:
                mismatches.append(f"Tool '{tool_name}' was not called, arguments missing.")
                total_args += max(len(expected_args), 1)
                continue

            actual_args = matching_actual.get("arguments", {})

            for key, exp_val in expected_args.items():
                total_args += 1
                if key in actual_args and values_match(exp_val, actual_args[key]):
                    matched_args += 1
                else:
                    act_val = actual_args.get(key)
                    mismatches.append(
                        f"In tool '{tool_name}': expected {key}='{exp_val}', got '{act_val}'"
                    )

        if total_args == 0:
            score = 1.0
        else:
            score = round(matched_args / total_args, 4)

        passed = (score >= 0.8)
        explanation = f"Argument accuracy: {score * 100:.1f}% ({matched_args}/{total_args} arguments matched)."
        if mismatches:
            explanation += f" Mismatches: {'; '.join(mismatches[:3])}"

        return EvaluatorResult(
            metric_name="tool_argument",
            metric_value=score,
            passed=passed,
            explanation=explanation,
            evidence={
                "matched_count": matched_args,
                "total_count": total_args,
                "mismatches": mismatches
            },
            failure_category="tool_argument_mismatch" if not passed else None
        )
