from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class EvaluationReportResponse(BaseModel):
    run_id: str
    run_name: str
    created_at: datetime
    completed_at: Optional[datetime]
    agent_info: Dict[str, Any]
    dataset_info: Dict[str, Any]
    summary_metrics: Dict[str, Any]
    test_results_summary: List[Dict[str, Any]]
    failure_breakdown: Dict[str, int]
    executive_summary: str
    recommendations: List[str]
