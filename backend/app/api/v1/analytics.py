from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.v1.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.analytics import OverviewMetricsResponse
from app.schemas.evaluation import RunComparisonRequest, RunComparisonResponse
from app.services.analytics_service import AnalyticsService
from app.services.comparison_service import ComparisonService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=OverviewMetricsResponse)
def get_analytics_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve high-level metrics, trends, and charts calculated from stored evaluation data."""
    return AnalyticsService.get_overview(db, current_user.id)


@router.post("/compare", response_model=RunComparisonResponse)
def compare_runs(
    compare_req: RunComparisonRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Benchmark and compare two evaluation runs side-by-side with delta analysis and metric winners."""
    return ComparisonService.compare_runs(
        db, current_user.id, compare_req.run_id_a, compare_req.run_id_b
    )
