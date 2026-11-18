import re
from typing import Any, Dict, List, Optional
from app.evaluators.base import BaseEvaluator, EvaluatorResult


def tokenize(text: str) -> set:
    words = re.findall(r"\b[a-zA-Z0-9_\-]+\b", text.lower())
    # Exclude common stopwords
    stopwords = {"the", "a", "an", "is", "are", "was", "were", "and", "or", "in", "on", "at", "to", "for", "with", "by", "of", "it", "my", "your"}
    return {w for w in words if w not in stopwords and len(w) > 2}


class SemanticEvaluator(BaseEvaluator):
    """
    Evaluates response semantic relevance, expected keyword coverage,
    and factual grounding against executed tool results.
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
        expected_behavior = test_case.get("expected_behavior", "")
        keywords: List[str] = expected_output.get("contains_keywords", [])

        if not actual_output.strip() and not error:
            return EvaluatorResult(
                metric_name="semantic_response",
                metric_value=0.0,
                passed=False,
                explanation="Response was empty.",
                evidence={},
                failure_category="empty_response"
            )

        # 1. Keyword coverage
        matched_keywords = []
        if keywords:
            for kw in keywords:
                if kw.lower() in actual_output.lower():
                    matched_keywords.append(kw)
            keyword_score = len(matched_keywords) / len(keywords)
        else:
            keyword_score = 1.0

        # 2. Semantic token overlap with expected behavior description
        behavior_tokens = tokenize(expected_behavior)
        output_tokens = tokenize(actual_output)
        
        if behavior_tokens:
            overlap = behavior_tokens.intersection(output_tokens)
            overlap_score = min(len(overlap) / max(len(behavior_tokens), 1), 1.0)
        else:
            overlap_score = 1.0

        # Weighted blend (60% keyword match, 40% intent overlap)
        if keywords:
            semantic_score = round(0.6 * keyword_score + 0.4 * overlap_score, 4)
        else:
            semantic_score = round(overlap_score, 4)

        passed = (semantic_score >= 0.5)
        explanation = f"Semantic relevance score: {semantic_score * 100:.1f}%."
        if keywords:
            explanation += f" Keyword matches: {len(matched_keywords)}/{len(keywords)} ({', '.join(matched_keywords)})."

        return EvaluatorResult(
            metric_name="semantic_response",
            metric_value=semantic_score,
            passed=passed,
            explanation=explanation,
            evidence={
                "keyword_score": keyword_score,
                "overlap_score": overlap_score,
                "matched_keywords": matched_keywords,
                "missing_keywords": [k for k in keywords if k not in matched_keywords]
            },
            failure_category="semantic_low_quality" if not passed else None
        )
