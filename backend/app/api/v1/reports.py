from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from app.api.v1.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.reports import EvaluationReportResponse
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/{run_id}", response_model=EvaluationReportResponse)
def get_evaluation_report(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate comprehensive evaluation report including executive summary and recommendations."""
    return ReportService.generate_report(db, run_id, current_user.id)


@router.get("/{run_id}/export")
def export_evaluation_report(
    run_id: str,
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download evaluation report in CSV or JSON format."""
    if format == "csv":
        csv_data = ReportService.export_csv(db, run_id, current_user.id)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=agentbench_report_{run_id}.csv"}
        )
    else:
        report = ReportService.generate_report(db, run_id, current_user.id)
        return Response(
            content=report.model_dump_json(indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=agentbench_report_{run_id}.json"}
        )
