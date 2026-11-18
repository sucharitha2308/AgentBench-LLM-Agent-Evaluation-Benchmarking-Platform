from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel


class EvaluatorResult(BaseModel):
    metric_name: str
    metric_value: float  # Normalized numeric score (e.g. 0.0 to 1.0, or count)
    passed: bool
    explanation: str
    evidence: Dict[str, Any] = {}
    failure_category: Optional[str] = None


class BaseEvaluator(ABC):
    @abstractmethod
    def evaluate(
        self,
        test_case: Dict[str, Any],
        actual_output: str,
        actual_tool_calls: list,
        actual_tool_results: list,
        duration_ms: int,
        error: Optional[str] = None
    ) -> EvaluatorResult:
        """Run evaluation and return structured EvaluatorResult."""
        pass
