from typing import Any, Dict, List
from fastapi import APIRouter, Depends, status, Body
from sqlalchemy.orm import Session
from app.api.v1.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.dataset import (
    DatasetCreate, DatasetUpdate, DatasetResponse,
    TestCaseCreate, TestCaseUpdate, TestCaseResponse,
    DatasetVersionResponse, DatasetExportResponse
)
from app.services.dataset_service import DatasetService

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
def create_dataset(
    dataset_in: DatasetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new evaluation dataset."""
    return DatasetService.create_dataset(db, current_user.id, dataset_in)


@router.get("", response_model=List[DatasetResponse])
def list_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List datasets accessible to current user."""
    datasets = DatasetService.list_datasets(db, current_user.id)
    res = []
    for d in datasets:
        resp = DatasetResponse.model_validate(d)
        resp.test_case_count = len(d.test_cases)
        res.append(resp)
    return res


@router.get("/{id}", response_model=DatasetResponse)
def get_dataset(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve dataset details."""
    d = DatasetService.get_dataset(db, id, current_user.id)
    resp = DatasetResponse.model_validate(d)
    resp.test_case_count = len(d.test_cases)
    return resp


@router.put("/{id}", response_model=DatasetResponse)
def update_dataset(
    id: str,
    dataset_in: DatasetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update dataset metadata."""
    d = DatasetService.update_dataset(db, id, current_user.id, dataset_in)
    resp = DatasetResponse.model_validate(d)
    resp.test_case_count = len(d.test_cases)
    return resp


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete dataset and all associated test cases."""
    DatasetService.delete_dataset(db, id, current_user.id)
    return None


@router.get("/{id}/test-cases", response_model=List[TestCaseResponse])
def list_test_cases(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all test cases in dataset."""
    return DatasetService.list_test_cases(db, id, current_user.id)


@router.post("/{id}/test-cases", response_model=TestCaseResponse, status_code=status.HTTP_201_CREATED)
def add_test_case(
    id: str,
    tc_in: TestCaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a test case to dataset."""
    return DatasetService.add_test_case(db, id, current_user.id, tc_in)


@router.put("/{id}/test-cases/{tc_id}", response_model=TestCaseResponse)
def update_test_case(
    id: str,
    tc_id: str,
    tc_in: TestCaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a specific test case."""
    return DatasetService.update_test_case(db, id, tc_id, current_user.id, tc_in)


@router.delete("/{id}/test-cases/{tc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test_case(
    id: str,
    tc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove test case from dataset."""
    DatasetService.delete_test_case(db, id, tc_id, current_user.id)
    return None


@router.post("/{id}/versions", response_model=DatasetVersionResponse)
def create_dataset_version(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create an immutable snapshot version of the current dataset."""
    return DatasetService.create_version(db, id, current_user.id)


@router.get("/{id}/export", response_model=DatasetExportResponse)
def export_dataset(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export complete dataset and test cases in standard JSON format."""
    return DatasetService.export_dataset(db, id, current_user.id)


@router.post("/{id}/import")
def import_dataset(
    id: str,
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Import test cases from a structured JSON dataset file."""
    count = DatasetService.import_dataset(db, id, current_user.id, data)
    return {"success": True, "imported_count": count}
