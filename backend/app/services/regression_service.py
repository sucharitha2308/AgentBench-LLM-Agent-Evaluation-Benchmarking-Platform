from typing import Any, Dict, List
from sqlalchemy.orm import Session
from app.models.evaluation import EvaluationRun, TestResult
from app.schemas.evaluation import RegressionAnalysisResponse
from app.core.errors import NotFoundException, ForbiddenException


class RegressionService:
    @staticmethod
    def analyze_regressions(
        db: Session,
        user_id: str,
        baseline_run_id: str,
        current_run_id: str,
        threshold_pct: float = 5.0
    ) -> RegressionAnalysisResponse:
        baseline_run = db.query(EvaluationRun).filter(EvaluationRun.id == baseline_run_id).first()
        current_run = db.query(EvaluationRun).filter(EvaluationRun.id == current_run_id).first()

        if not baseline_run:
            raise NotFoundException("Baseline Run", baseline_run_id)
        if not current_run:
            raise NotFoundException("Current Run", current_run_id)

        if baseline_run.user_id != user_id or current_run.user_id != user_id:
            raise ForbiddenException()

        baseline_results = {
            tr.test_case_identifier: tr
            for tr in db.query(TestResult).filter(TestResult.evaluation_run_id == baseline_run_id).all()
        }
        current_results = {
            tr.test_case_identifier: tr
            for tr in db.query(TestResult).filter(TestResult.evaluation_run_id == current_run_id).all()
        }

        regressed_cases: List[Dict[str, Any]] = []

        for tid, base_tr in baseline_results.items():
            curr_tr = current_results.get(tid)
            if not curr_tr:
                continue

            # Regressed: Was PASS in baseline, but is now FAIL or ERROR
            if base_tr.status == "PASS" and curr_tr.status in ["FAIL", "ERROR"]:
                regressed_cases.append({
                    "test_case_identifier": tid,
                    "name": base_tr.name,
                    "previous_status": base_tr.status,
                    "current_status": curr_tr.status,
                    "previous_latency_ms": base_tr.duration_ms,
                    "current_latency_ms": curr_tr.duration_ms,
                    "failure_category": curr_tr.failure_category,
                    "failure_explanation": curr_tr.failure_explanation
                })

        # Metric degradations
        b_metrics = baseline_run.aggregate_metrics or {}
        c_metrics = current_run.aggregate_metrics or {}
        metric_degradations: List[Dict[str, Any]] = []

        key_metrics = [
            ("task_success_rate", "Task Success Rate"),
            ("tool_selection_accuracy", "Tool Selection Accuracy"),
            ("structured_output_validity", "JSON Output Validity"),
            ("semantic_score", "Semantic Quality Score"),
            ("average_latency_ms", "Average Latency"),
        ]

        for metric_key, label in key_metrics:
            base_val = float(b_metrics.get(metric_key, 0.0))
            curr_val = float(c_metrics.get(metric_key, 0.0))

            if metric_key == "average_latency_ms":
                # Latency regression if increased
                if curr_val > base_val and base_val > 0:
                    increase_pct = ((curr_val - base_val) / base_val) * 100
                    if increase_pct >= threshold_pct:
                        metric_degradations.append({
                            "metric": label,
                            "baseline": f"{base_val:.1f}ms",
                            "current": f"{curr_val:.1f}ms",
                            "degradation": f"+{increase_pct:.1f}% latency spike"
                        })
            else:
                # Accuracy regression if decreased
                if curr_val < base_val:
                    drop = base_val - curr_val
                    if drop >= threshold_pct:
                        metric_degradations.append({
                            "metric": label,
                            "baseline": f"{base_val:.1f}%",
                            "current": f"{curr_val:.1f}%",
                            "degradation": f"-{drop:.1f}% drop"
                        })

        # Determine severity
        reg_count = len(regressed_cases)
        has_major_metric_drop = any(
            ("drop" in d.get("degradation", "").lower() and float(d["degradation"].split("%")[0].replace("-", "").strip()) > 15)
            for d in metric_degradations
        )
        if reg_count == 0 and not metric_degradations:
            severity = "LOW"
            recommendation = "No performance regressions detected. Safe to deploy or promote agent configuration."
        elif reg_count <= 2 and len(metric_degradations) <= 1:
            severity = "MEDIUM"
            recommendation = "Minor regressions observed in isolated test cases. Review tool argument bindings and prompt modifications before deploying."
        elif reg_count <= 5 or has_major_metric_drop:
            severity = "HIGH"
            recommendation = "Noticeable regressions detected across several functional paths. Do not promote configuration until failing test cases are investigated."
        else:
            severity = "CRITICAL"
            recommendation = "Severe performance drop detected. Roll back agent modifications to the previous baseline version."

        return RegressionAnalysisResponse(
            baseline_run_id=baseline_run_id,
            current_run_id=current_run_id,
            total_regressions=reg_count,
            severity=severity,
            regressed_cases=regressed_cases,
            metric_degradations=metric_degradations,
            recommendation=recommendation
        )
