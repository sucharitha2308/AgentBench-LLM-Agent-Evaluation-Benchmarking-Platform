import csv
import io
import json
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from app.models.evaluation import EvaluationRun, TestResult
from app.schemas.reports import EvaluationReportResponse
from app.core.errors import NotFoundException, ForbiddenException


class ReportService:
    @staticmethod
    def generate_report(db: Session, run_id: str, user_id: str) -> EvaluationReportResponse:
        run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
        if not run:
            raise NotFoundException("EvaluationRun", run_id)
        if run.user_id != user_id:
            raise ForbiddenException()

        test_results = db.query(TestResult).filter(TestResult.evaluation_run_id == run_id).all()
        
        # Breakdown failures
        failure_breakdown: Dict[str, int] = {}
        for tr in test_results:
            if tr.status != "PASS":
                cat = tr.failure_category or "unknown_error"
                failure_breakdown[cat] = failure_breakdown.get(cat, 0) + 1

        # Synthesize executive summary & recommendations from actual data
        metrics = run.aggregate_metrics or {}
        success_rate = metrics.get("task_success_rate", 0.0)
        tool_acc = metrics.get("tool_selection_accuracy", 100.0)
        json_val = metrics.get("structured_output_validity", 100.0)
        avg_lat = metrics.get("average_latency_ms", 0.0)

        agent_name = run.agent_snapshot.get("name", "AI Agent")
        dataset_name = run.dataset_snapshot.get("name", "Dataset")

        executive_summary = (
            f"Evaluation run '{run.name}' evaluated agent '{agent_name}' on '{dataset_name}' ({run.total_test_cases} test cases). "
            f"The agent achieved a task success rate of {success_rate}% with an average latency of {avg_lat}ms. "
            f"Tool selection accuracy scored {tool_acc}%, and structured JSON output validity was {json_val}%."
        )

        recommendations = []
        if success_rate < 80.0:
            recommendations.append("Overall task success is below 80%. Review high-frequency failure categories.")
        if tool_acc < 85.0:
            recommendations.append("Tool selection precision is suboptimal. Consider refining tool descriptions and adding few-shot examples in system prompts.")
        if json_val < 90.0:
            recommendations.append("JSON schema compliance failures observed. Enforce strict JSON output mode or Pydantic output parsers.")
        if avg_lat > 3000:
            recommendations.append(f"Average latency ({avg_lat:.0f}ms) exceeds the target 3000ms threshold. Evaluate faster model tiers or reduce prompt token lengths.")
        if not recommendations:
            recommendations.append("Agent benchmark performance meets all operational quality and safety thresholds.")

        results_summary = [
            {
                "test_case_identifier": tr.test_case_identifier,
                "name": tr.name,
                "status": tr.status,
                "duration_ms": tr.duration_ms,
                "estimated_cost": tr.estimated_cost,
                "failure_category": tr.failure_category,
                "failure_explanation": tr.failure_explanation
            }
            for tr in test_results
        ]

        return EvaluationReportResponse(
            run_id=run.id,
            run_name=run.name,
            created_at=run.created_at,
            completed_at=run.completed_at,
            agent_info=run.agent_snapshot,
            dataset_info=run.dataset_snapshot,
            summary_metrics=metrics,
            test_results_summary=results_summary,
            failure_breakdown=failure_breakdown,
            executive_summary=executive_summary,
            recommendations=recommendations
        )

    @staticmethod
    def export_csv(db: Session, run_id: str, user_id: str) -> str:
        report = ReportService.generate_report(db, run_id, user_id)
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["Test Case ID", "Name", "Status", "Duration (ms)", "Estimated Cost ($)", "Failure Category", "Explanation"])
        for tc in report.test_results_summary:
            writer.writerow([
                tc["test_case_identifier"],
                tc["name"],
                tc["status"],
                tc["duration_ms"],
                f"{tc['estimated_cost']:.6f}",
                tc.get("failure_category", "") or "",
                tc.get("failure_explanation", "") or ""
            ])

        return output.getvalue()
