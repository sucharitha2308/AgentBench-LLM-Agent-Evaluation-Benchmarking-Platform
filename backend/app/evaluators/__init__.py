from typing import Dict
from app.evaluators.base import BaseEvaluator, EvaluatorResult
from app.evaluators.task_success import TaskSuccessEvaluator
from app.evaluators.tool_selection import ToolSelectionEvaluator
from app.evaluators.tool_argument import ToolArgumentEvaluator
from app.evaluators.structured_output import StructuredOutputEvaluator
from app.evaluators.semantic import SemanticEvaluator
from app.evaluators.performance import PerformanceEvaluator
from app.evaluators.reliability import ReliabilityEvaluator
from app.evaluators.safety import SafetyEvaluator
from app.evaluators.llm_judge import LLMJudgeEvaluator


EVALUATOR_REGISTRY: Dict[str, BaseEvaluator] = {
    "task_success": TaskSuccessEvaluator(),
    "tool_selection": ToolSelectionEvaluator(),
    "tool_argument": ToolArgumentEvaluator(),
    "structured_output": StructuredOutputEvaluator(),
    "semantic": SemanticEvaluator(),
    "performance": PerformanceEvaluator(),
    "reliability": ReliabilityEvaluator(),
    "safety": SafetyEvaluator(),
    "llm_judge": LLMJudgeEvaluator(),
}


def get_evaluator(name: str) -> BaseEvaluator:
    return EVALUATOR_REGISTRY.get(name.lower().strip())


__all__ = [
    "BaseEvaluator",
    "EvaluatorResult",
    "TaskSuccessEvaluator",
    "ToolSelectionEvaluator",
    "ToolArgumentEvaluator",
    "StructuredOutputEvaluator",
    "SemanticEvaluator",
    "PerformanceEvaluator",
    "ReliabilityEvaluator",
    "SafetyEvaluator",
    "LLMJudgeEvaluator",
    "EVALUATOR_REGISTRY",
    "get_evaluator",
]
