from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.api.v1.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.evaluation import (
    EvaluationCreate, EvaluationRunResponse, TestResultResponse,
    ExecutionTraceResponse, RegressionAnalysisResponse
)
from app.services.evaluation_service import EvaluationService
from app.services.regression_service import RegressionService

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])


@router.post("", response_model=EvaluationRunResponse, status_code=status.HTTP_201_CREATED)
def create_evaluation(
    eval_in: EvaluationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Launch a new evaluation run across selected evaluators."""
    return EvaluationService.create_run(db, current_user.id, eval_in)


@router.get("", response_model=List[EvaluationRunResponse])
def list_evaluations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List evaluation runs for current user."""
    return EvaluationService.list_runs(db, current_user.id)


@router.get("/regression/analyze", response_model=RegressionAnalysisResponse)
def analyze_regressions(
    baseline_run_id: str = Query(...),
    current_run_id: str = Query(...),
    threshold_pct: float = Query(5.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze performance regression between baseline and current evaluation run."""
    return RegressionService.analyze_regressions(
        db, current_user.id, baseline_run_id, current_run_id, threshold_pct
    )


@router.get("/traces/{trace_id}", response_model=ExecutionTraceResponse)
def get_single_trace(
    trace_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve full timeline steps for an individual test case trace."""
    return EvaluationService.get_trace_by_id(db, trace_id, current_user.id)


@router.get("/{id}", response_model=EvaluationRunResponse)
def get_evaluation(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve evaluation run progress, status, and aggregate metrics."""
    return EvaluationService.get_run(db, id, current_user.id)


@router.post("/{id}/cancel", response_model=EvaluationRunResponse)
def cancel_evaluation(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel an ongoing evaluation run."""
    return EvaluationService.cancel_run(db, id, current_user.id)


@router.get("/{id}/results", response_model=List[TestResultResponse])
def get_evaluation_results(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve detailed individual test results with evaluator scores and failure categories."""
    return EvaluationService.get_run_results(db, id, current_user.id)


@router.get("/{id}/traces", response_model=List[ExecutionTraceResponse])
def get_evaluation_traces(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve execution traces for an evaluation run."""
    return EvaluationService.get_run_traces(db, id, current_user.id)
