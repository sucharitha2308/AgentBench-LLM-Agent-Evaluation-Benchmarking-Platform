from typing import Any, Dict, List
from sqlalchemy.orm import Session
from app.models.evaluation import EvaluationRun, TestResult
from app.schemas.evaluation import RunComparisonResponse, MetricDelta, EvaluationRunResponse
from app.core.errors import NotFoundException, ForbiddenException, BadRequestException


METRIC_DIRECTIONS = {
    # True = higher is better; False = lower is better
    "task_success_rate": True,
    "tool_selection_accuracy": True,
    "tool_argument_accuracy": True,
    "structured_output_validity": True,
    "semantic_score": True,
    "safety_pass_rate": True,
    "average_latency_ms": False,
    "p50_latency_ms": False,
    "p95_latency_ms": False,
    "total_tokens": False,
    "estimated_cost_usd": False,
    "error_rate": False,
}


class ComparisonService:
    @staticmethod
    def compare_runs(db: Session, user_id: str, run_id_a: str, run_id_b: str) -> RunComparisonResponse:
        run_a = db.query(EvaluationRun).filter(EvaluationRun.id == run_id_a).first()
        run_b = db.query(EvaluationRun).filter(EvaluationRun.id == run_id_b).first()

        if not run_a:
            raise NotFoundException("EvaluationRun A", run_id_a)
        if not run_b:
            raise NotFoundException("EvaluationRun B", run_id_b)

        if run_a.user_id != user_id or run_b.user_id != user_id:
            raise ForbiddenException("You cannot compare evaluation runs belonging to another user.")

        metrics_a = run_a.aggregate_metrics or {}
        metrics_b = run_b.aggregate_metrics or {}

        metric_deltas: List[MetricDelta] = []
        wins_a = 0
        wins_b = 0

        for metric_name, higher_is_better in METRIC_DIRECTIONS.items():
            val_a = float(metrics_a.get(metric_name, 0.0))
            val_b = float(metrics_b.get(metric_name, 0.0))
            delta = round(val_b - val_a, 4)

            if val_a != 0:
                pct_change = round(((val_b - val_a) / abs(val_a)) * 100, 2)
            else:
                pct_change = 0.0 if val_b == 0 else 100.0

            if val_a == val_b:
                winner = "TIE"
            elif higher_is_better:
                winner = "B" if val_b > val_a else "A"
            else:
                winner = "B" if val_b < val_a else "A"

            if winner == "A":
                wins_a += 1
            elif winner == "B":
                wins_b += 1

            metric_deltas.append(MetricDelta(
                metric_name=metric_name,
                value_a=val_a,
                value_b=val_b,
                delta=delta,
                percentage_change=pct_change,
                winner=winner
            ))

        # Test-level comparison
        results_a = {
            tr.test_case_identifier: tr
            for tr in db.query(TestResult).filter(TestResult.evaluation_run_id == run_id_a).all()
        }
        results_b = {
            tr.test_case_identifier: tr
            for tr in db.query(TestResult).filter(TestResult.evaluation_run_id == run_id_b).all()
        }

        test_differences = []
        all_ids = set(results_a.keys()).union(set(results_b.keys()))

        for tid in sorted(all_ids):
            ra = results_a.get(tid)
            rb = results_b.get(tid)
            status_a = ra.status if ra else "NOT_RUN"
            status_b = rb.status if rb else "NOT_RUN"
            
            lat_a = ra.duration_ms if ra else 0
            lat_b = rb.duration_ms if rb else 0

            test_differences.append({
                "test_case_identifier": tid,
                "name": ra.name if ra else (rb.name if rb else tid),
                "status_a": status_a,
                "status_b": status_b,
                "status_differs": (status_a != status_b),
                "latency_a_ms": lat_a,
                "latency_b_ms": lat_b,
                "latency_delta_ms": lat_b - lat_a,
                "failure_category_a": ra.failure_category if ra else None,
                "failure_category_b": rb.failure_category if rb else None,
            })

        # Summary text
        name_a = run_a.agent_snapshot.get("name", run_a.name)
        name_b = run_b.agent_snapshot.get("name", run_b.name)
        if wins_a > wins_b:
            summary = f"Agent '{name_a}' outperforms '{name_b}' on {wins_a} out of {len(metric_deltas)} key metrics."
        elif wins_b > wins_a:
            summary = f"Agent '{name_b}' outperforms '{name_a}' on {wins_b} out of {len(metric_deltas)} key metrics."
        else:
            summary = f"Agents '{name_a}' and '{name_b}' showed equivalent overall benchmark performance."

        return RunComparisonResponse(
            run_a=EvaluationRunResponse.model_validate(run_a),
            run_b=EvaluationRunResponse.model_validate(run_b),
            metric_comparisons=metric_deltas,
            test_differences=test_differences,
            summary=summary
        )
