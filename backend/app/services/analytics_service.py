from typing import Any, Dict, List
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.agent import Agent
from app.models.dataset import Dataset, TestCase
from app.models.evaluation import EvaluationRun, TestResult
from app.schemas.analytics import OverviewMetricsResponse, RunAnalyticsResponse


class AnalyticsService:
    @staticmethod
    def get_overview(db: Session, user_id: str) -> OverviewMetricsResponse:
        total_agents = db.query(Agent).filter((Agent.user_id == user_id) | (Agent.is_sample == True)).count()
        total_datasets = db.query(Dataset).filter((Dataset.user_id == user_id) | (Dataset.is_sample == True)).count()
        
        runs = db.query(EvaluationRun).filter(
            EvaluationRun.user_id == user_id,
            EvaluationRun.status == "COMPLETED"
        ).order_by(EvaluationRun.created_at.desc()).all()

        total_runs = len(runs)
        
        # Calculate totals and averages from actual stored data
        total_executed = sum(r.completed_test_cases for r in runs)
        total_passed = sum(r.passed_test_cases for r in runs)
        total_failed = sum(r.failed_test_cases for r in runs)

        overall_success_rate = round((total_passed / total_executed * 100), 2) if total_executed > 0 else 0.0
        overall_failure_rate = round((total_failed / total_executed * 100), 2) if total_executed > 0 else 0.0

        latencies = [
            float(r.aggregate_metrics.get("average_latency_ms", 0.0))
            for r in runs if r.aggregate_metrics and "average_latency_ms" in r.aggregate_metrics
        ]
        avg_latency = round(float(np.mean(latencies)), 2) if latencies else 0.0
        p95_latencies = [
            float(r.aggregate_metrics.get("p95_latency_ms", 0.0))
            for r in runs if r.aggregate_metrics and "p95_latency_ms" in r.aggregate_metrics
        ]
        p95_latency = round(float(np.mean(p95_latencies)), 2) if p95_latencies else 0.0

        total_tokens = sum(
            int(r.aggregate_metrics.get("total_tokens", 0))
            for r in runs if r.aggregate_metrics
        )
        total_cost = sum(
            float(r.aggregate_metrics.get("estimated_cost_usd", 0.0))
            for r in runs if r.aggregate_metrics
        )

        tool_accuracies = [
            float(r.aggregate_metrics.get("tool_selection_accuracy", 100.0))
            for r in runs if r.aggregate_metrics and "tool_selection_accuracy" in r.aggregate_metrics
        ]
        avg_tool_acc = round(float(np.mean(tool_accuracies)), 2) if tool_accuracies else 100.0

        json_validities = [
            float(r.aggregate_metrics.get("structured_output_validity", 100.0))
            for r in runs if r.aggregate_metrics and "structured_output_validity" in r.aggregate_metrics
        ]
        avg_json_val = round(float(np.mean(json_validities)), 2) if json_validities else 100.0

        # Recent runs list
        recent_runs = [
            {
                "id": r.id,
                "name": r.name,
                "agent_name": r.agent_snapshot.get("name", "Unknown Agent"),
                "status": r.status,
                "success_rate": r.aggregate_metrics.get("task_success_rate", 0.0) if r.aggregate_metrics else 0.0,
                "created_at": r.created_at.isoformat(),
                "total_cases": r.total_test_cases,
                "passed": r.passed_test_cases,
                "failed": r.failed_test_cases
            }
            for r in runs[:8]
        ]

        # Success trend over time (chronological)
        success_trend = [
            {
                "run_name": r.name,
                "success_rate": r.aggregate_metrics.get("task_success_rate", 0.0),
                "avg_latency": r.aggregate_metrics.get("average_latency_ms", 0.0),
                "date": r.created_at.strftime("%b %d %H:%M")
            }
            for r in reversed(runs[:12])
            if r.aggregate_metrics
        ]

        # Failure distribution across categories
        all_failed_results = db.query(TestResult).join(EvaluationRun).filter(
            EvaluationRun.user_id == user_id,
            TestResult.status.in_(["FAIL", "ERROR"])
        ).all()

        category_counts: Dict[str, int] = {}
        for tr in all_failed_results:
            cat = tr.failure_category or "other_error"
            category_counts[cat] = category_counts.get(cat, 0) + 1

        failure_distribution = [
            {"category": cat.replace("_", " ").title(), "count": count}
            for cat, count in category_counts.items()
        ]

        # Model comparison overview
        model_runs: Dict[str, List[float]] = {}
        for r in runs:
            m_name = r.agent_snapshot.get("model_name", "unknown")
            s_rate = r.aggregate_metrics.get("task_success_rate", 0.0) if r.aggregate_metrics else 0.0
            model_runs.setdefault(m_name, []).append(s_rate)

        model_comparison = [
            {
                "model": model,
                "avg_success_rate": round(float(np.mean(scores)), 2),
                "runs_count": len(scores)
            }
            for model, scores in model_runs.items()
        ]

        return OverviewMetricsResponse(
            total_agents=total_agents,
            total_datasets=total_datasets,
            total_evaluation_runs=total_runs,
            total_test_cases_executed=total_executed,
            overall_success_rate=overall_success_rate,
            overall_failure_rate=overall_failure_rate,
            average_latency_ms=avg_latency,
            p95_latency_ms=p95_latency,
            total_tokens_consumed=total_tokens,
            total_estimated_cost_usd=round(total_cost, 4),
            average_tool_selection_accuracy=avg_tool_acc,
            average_json_validity_rate=avg_json_val,
            recent_runs=recent_runs,
            success_trend=success_trend,
            failure_distribution=failure_distribution,
            model_comparison_overview=model_comparison
        )
