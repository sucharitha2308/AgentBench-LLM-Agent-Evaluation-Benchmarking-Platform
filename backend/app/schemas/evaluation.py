from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EvaluationCreate(BaseModel):
    agent_id: str
    dataset_id: str
    name: str = Field(..., min_length=2, max_length=255)
    concurrency_limit: int = Field(default=5, ge=1, le=20)
    timeout_seconds: int = Field(default=30, ge=5, le=120)
    selected_evaluators: List[str] = Field(
        default_factory=lambda: [
            "task_success",
            "tool_selection",
            "tool_argument",
            "structured_output",
            "semantic",
            "performance",
            "reliability",
            "safety"
        ]
    )


class EvaluationRunResponse(BaseModel):
    id: str
    user_id: str
    agent_id: str
    dataset_id: str
    agent_version_id: Optional[str] = None
    dataset_version_id: Optional[str] = None
    name: str
    status: str
    total_test_cases: int
    completed_test_cases: int
    passed_test_cases: int
    failed_test_cases: int
    error_count: int
    aggregate_metrics: Dict[str, Any]
    agent_snapshot: Dict[str, Any]
    dataset_snapshot: Dict[str, Any]
    concurrency_limit: int
    timeout_seconds: int
    selected_evaluators: List[str]
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestResultResponse(BaseModel):
    id: str
    evaluation_run_id: str
    test_case_id: Optional[str] = None
    test_case_identifier: str
    name: str
    status: str
    duration_ms: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost: float
    actual_response: str
    actual_tool_calls: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    failure_category: Optional[str] = None
    failure_explanation: Optional[str] = None
    trace_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ExecutionTraceResponse(BaseModel):
    id: str
    evaluation_run_id: str
    test_result_id: Optional[str] = None
    test_case_identifier: str
    steps: List[Dict[str, Any]]
    redacted_secrets_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class RunComparisonRequest(BaseModel):
    run_id_a: str
    run_id_b: str


class MetricDelta(BaseModel):
    metric_name: str
    value_a: float
    value_b: float
    delta: float
    percentage_change: float
    winner: str  # "A", "B", "TIE"


class RunComparisonResponse(BaseModel):
    run_a: EvaluationRunResponse
    run_b: EvaluationRunResponse
    metric_comparisons: List[MetricDelta]
    test_differences: List[Dict[str, Any]]
    summary: str


class RegressionAnalysisResponse(BaseModel):
    baseline_run_id: str
    current_run_id: str
    total_regressions: int
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    regressed_cases: List[Dict[str, Any]]
    metric_degradations: List[Dict[str, Any]]
    recommendation: str


class CredentialCreate(BaseModel):
    provider_name: str = Field(..., pattern="^(openai|gemini)$")
    api_key: str = Field(..., min_length=10)
    key_alias: str = "Default Key"


class CredentialResponse(BaseModel):
    id: str
    provider_name: str
    key_alias: str
    is_valid: bool
    last_verified_at: Optional[datetime] = None
    created_at: datetime
    # Notice: raw api_key is NEVER returned! Masked preview only.
    masked_key: str

    class Config:
        from_attributes = True
