import json
import re
from typing import Any, Dict, Optional
import jsonschema
from app.evaluators.base import BaseEvaluator, EvaluatorResult


class StructuredOutputEvaluator(BaseEvaluator):
    """
    Validates agent output against JSON schema constraints, required fields, and types.
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
        expected_output = test_case.get("expected_output", {}) or {}
        schema = expected_output.get("schema")

        # If this test case does not require JSON schema, it's considered valid
        if not schema:
            return EvaluatorResult(
                metric_name="structured_output",
                metric_value=1.0,
                passed=True,
                explanation="No structured JSON schema constraints enforced for this test case.",
                evidence={"schema_enforced": False}
            )

        # Attempt to extract JSON from markdown code fences or raw string
        extracted_json = None
        cleaned_text = actual_output.strip()
        
        # Check for ```json ... ``` code fence
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned_text)
        if fence_match:
            raw_json = fence_match.group(1).strip()
        else:
            raw_json = cleaned_text

        try:
            extracted_json = json.loads(raw_json)
        except json.JSONDecodeError as jde:
            return EvaluatorResult(
                metric_name="structured_output",
                metric_value=0.0,
                passed=False,
                explanation=f"Failed to parse response as valid JSON: {str(jde)}",
                evidence={"raw_snippet": cleaned_text[:200], "error": str(jde)},
                failure_category="json_syntax_error"
            )

        # Validate against JSON schema
        try:
            jsonschema.validate(instance=extracted_json, schema=schema)
            return EvaluatorResult(
                metric_name="structured_output",
                metric_value=1.0,
                passed=True,
                explanation="Output strictly conforms to the expected JSON schema and data types.",
                evidence={"parsed_json": extracted_json}
            )
        except jsonschema.ValidationError as ve:
            return EvaluatorResult(
                metric_name="structured_output",
                metric_value=0.0,
                passed=False,
                explanation=f"JSON schema validation failed: {ve.message} at path '{list(ve.path)}'",
                evidence={"validation_error": ve.message, "path": list(ve.path), "parsed_json": extracted_json},
                failure_category="json_schema_violation"
            )
        except Exception as e:
            return EvaluatorResult(
                metric_name="structured_output",
                metric_value=0.0,
                passed=False,
                explanation=f"Schema validation error: {str(e)}",
                evidence={"error": str(e)},
                failure_category="json_schema_violation"
            )
