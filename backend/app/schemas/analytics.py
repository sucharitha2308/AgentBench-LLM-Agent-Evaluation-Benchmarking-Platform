from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class OverviewMetricsResponse(BaseModel):
    total_agents: int
    total_datasets: int
    total_evaluation_runs: int
    total_test_cases_executed: int
    overall_success_rate: float
    overall_failure_rate: float
    average_latency_ms: float
    p95_latency_ms: float
    total_tokens_consumed: int
    total_estimated_cost_usd: float
    average_tool_selection_accuracy: float
    average_json_validity_rate: float
    
    # Trends and Charts
    recent_runs: List[Dict[str, Any]]
    success_trend: List[Dict[str, Any]]
    failure_distribution: List[Dict[str, Any]]
    model_comparison_overview: List[Dict[str, Any]]


class RunAnalyticsResponse(BaseModel):
    run_id: str
    run_name: str
    agent_name: str
    dataset_name: str
    metrics: Dict[str, Any]
    latency_histogram: List[Dict[str, Any]]
    category_breakdown: List[Dict[str, Any]]
    tool_usage_summary: Dict[str, Any]
