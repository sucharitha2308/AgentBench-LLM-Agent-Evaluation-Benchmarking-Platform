import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.dataset import Dataset, DatasetVersion, TestCase
from app.schemas.dataset import (
    DatasetCreate, DatasetUpdate, TestCaseCreate, TestCaseUpdate, DatasetExportResponse
)
from app.core.errors import NotFoundException, ForbiddenException, BadRequestException


class DatasetService:
    @staticmethod
    def list_datasets(db: Session, user_id: str) -> List[Dataset]:
        return db.query(Dataset).filter(
            (Dataset.user_id == user_id) | (Dataset.is_sample == True)
        ).order_by(Dataset.created_at.desc()).all()

    @staticmethod
    def get_dataset(db: Session, dataset_id: str, user_id: str) -> Dataset:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise NotFoundException("Dataset", dataset_id)
        if dataset.user_id != user_id and not dataset.is_sample:
            raise ForbiddenException()
        return dataset

    @staticmethod
    def create_dataset(db: Session, user_id: str, dataset_in: DatasetCreate) -> Dataset:
        dataset = Dataset(
            user_id=user_id,
            name=dataset_in.name,
            description=dataset_in.description,
            domain=dataset_in.domain,
            is_sample=False
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)

        test_cases_list = []
        if dataset_in.test_cases:
            for tc in dataset_in.test_cases:
                test_case = TestCase(
                    dataset_id=dataset.id,
                    test_case_id=tc.test_case_id,
                    name=tc.name,
                    description=tc.description,
                    user_input=tc.user_input,
                    difficulty_level=tc.difficulty_level,
                    tags=tc.tags,
                    expected_behavior=tc.expected_behavior,
                    expected_tool_calls=tc.expected_tool_calls,
                    expected_output=tc.expected_output,
                    max_allowed_latency_ms=tc.max_allowed_latency_ms,
                    evaluation_criteria=tc.evaluation_criteria
                )
                db.add(test_case)
                test_cases_list.append(tc.model_dump())
            db.commit()

        # Create initial dataset version snapshot
        version = DatasetVersion(
            dataset_id=dataset.id,
            version_number=1,
            test_case_count=len(test_cases_list),
            snapshot=test_cases_list
        )
        db.add(version)
        db.commit()
        return dataset

    @staticmethod
    def update_dataset(db: Session, dataset_id: str, user_id: str, dataset_in: DatasetUpdate) -> Dataset:
        dataset = DatasetService.get_dataset(db, dataset_id, user_id)
        if dataset.is_sample and dataset.user_id != user_id:
            raise ForbiddenException("Sample benchmark dataset is read-only.")

        update_data = dataset_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(dataset, field, value)

        db.commit()
        db.refresh(dataset)
        return dataset

    @staticmethod
    def delete_dataset(db: Session, dataset_id: str, user_id: str) -> None:
        dataset = DatasetService.get_dataset(db, dataset_id, user_id)
        if dataset.is_sample and dataset.user_id != user_id:
            raise ForbiddenException("Sample datasets cannot be deleted.")
        db.delete(dataset)
        db.commit()

    @staticmethod
    def list_test_cases(db: Session, dataset_id: str, user_id: str) -> List[TestCase]:
        DatasetService.get_dataset(db, dataset_id, user_id)
        return db.query(TestCase).filter(TestCase.dataset_id == dataset_id).order_by(TestCase.test_case_id).all()

    @staticmethod
    def add_test_case(db: Session, dataset_id: str, user_id: str, tc_in: TestCaseCreate) -> TestCase:
        dataset = DatasetService.get_dataset(db, dataset_id, user_id)
        if dataset.is_sample and dataset.user_id != user_id:
            raise ForbiddenException("Cannot add test cases to sample dataset.")

        existing = db.query(TestCase).filter(TestCase.dataset_id == dataset_id, TestCase.test_case_id == tc_in.test_case_id).first()
        if existing:
            raise BadRequestException(f"Test case with ID '{tc_in.test_case_id}' already exists in this dataset.")

        tc = TestCase(
            dataset_id=dataset_id,
            test_case_id=tc_in.test_case_id,
            name=tc_in.name,
            description=tc_in.description,
            user_input=tc_in.user_input,
            difficulty_level=tc_in.difficulty_level,
            tags=tc_in.tags,
            expected_behavior=tc_in.expected_behavior,
            expected_tool_calls=tc_in.expected_tool_calls,
            expected_output=tc_in.expected_output,
            max_allowed_latency_ms=tc_in.max_allowed_latency_ms,
            evaluation_criteria=tc_in.evaluation_criteria
        )
        db.add(tc)
        db.commit()
        db.refresh(tc)
        return tc

    @staticmethod
    def update_test_case(db: Session, dataset_id: str, test_case_id: str, user_id: str, tc_in: TestCaseUpdate) -> TestCase:
        DatasetService.get_dataset(db, dataset_id, user_id)
        tc = db.query(TestCase).filter(TestCase.dataset_id == dataset_id, TestCase.id == test_case_id).first()
        if not tc:
            raise NotFoundException("TestCase", test_case_id)

        update_data = tc_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tc, field, value)

        db.commit()
        db.refresh(tc)
        return tc

    @staticmethod
    def delete_test_case(db: Session, dataset_id: str, test_case_id: str, user_id: str) -> None:
        DatasetService.get_dataset(db, dataset_id, user_id)
        tc = db.query(TestCase).filter(TestCase.dataset_id == dataset_id, TestCase.id == test_case_id).first()
        if not tc:
            raise NotFoundException("TestCase", test_case_id)
        db.delete(tc)
        db.commit()

    @staticmethod
    def create_version(db: Session, dataset_id: str, user_id: str) -> DatasetVersion:
        dataset = DatasetService.get_dataset(db, dataset_id, user_id)
        test_cases = db.query(TestCase).filter(TestCase.dataset_id == dataset_id).all()
        
        last_v = db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset_id).order_by(DatasetVersion.version_number.desc()).first()
        next_ver = (last_v.version_number + 1) if last_v else 1

        snapshot = [
            {
                "test_case_id": tc.test_case_id,
                "name": tc.name,
                "description": tc.description,
                "user_input": tc.user_input,
                "difficulty_level": tc.difficulty_level,
                "tags": tc.tags,
                "expected_behavior": tc.expected_behavior,
                "expected_tool_calls": tc.expected_tool_calls,
                "expected_output": tc.expected_output,
                "max_allowed_latency_ms": tc.max_allowed_latency_ms,
                "evaluation_criteria": tc.evaluation_criteria
            }
            for tc in test_cases
        ]

        version = DatasetVersion(
            dataset_id=dataset_id,
            version_number=next_ver,
            test_case_count=len(test_cases),
            snapshot=snapshot
        )
        db.add(version)
        db.commit()
        db.refresh(version)
        return version

    @staticmethod
    def export_dataset(db: Session, dataset_id: str, user_id: str) -> DatasetExportResponse:
        dataset = DatasetService.get_dataset(db, dataset_id, user_id)
        test_cases = db.query(TestCase).filter(TestCase.dataset_id == dataset_id).all()
        
        formatted_cases = [
            {
                "test_case_id": tc.test_case_id,
                "name": tc.name,
                "description": tc.description,
                "user_input": tc.user_input,
                "difficulty_level": tc.difficulty_level,
                "tags": tc.tags,
                "expected_behavior": tc.expected_behavior,
                "expected_tool_calls": tc.expected_tool_calls,
                "expected_output": tc.expected_output,
                "max_allowed_latency_ms": tc.max_allowed_latency_ms,
                "evaluation_criteria": tc.evaluation_criteria
            }
            for tc in test_cases
        ]

        return DatasetExportResponse(
            dataset_name=dataset.name,
            description=dataset.description,
            domain=dataset.domain,
            version="1.0.0",
            exported_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            test_cases=formatted_cases
        )

    @staticmethod
    def import_dataset(db: Session, dataset_id: str, user_id: str, data: Dict[str, Any]) -> int:
        dataset = DatasetService.get_dataset(db, dataset_id, user_id)
        test_cases_data = data.get("test_cases", [])
        if not test_cases_data:
            raise BadRequestException("No test cases found in uploaded JSON.")

        imported_count = 0
        for tc in test_cases_data:
            test_id = tc.get("test_case_id")
            if not test_id:
                continue
            existing = db.query(TestCase).filter(TestCase.dataset_id == dataset_id, TestCase.test_case_id == test_id).first()
            if existing:
                continue

            test_case = TestCase(
                dataset_id=dataset_id,
                test_case_id=test_id,
                name=tc.get("name", f"Test {test_id}"),
                description=tc.get("description", ""),
                user_input=tc.get("user_input", ""),
                difficulty_level=tc.get("difficulty_level", "medium"),
                tags=tc.get("tags", []),
                expected_behavior=tc.get("expected_behavior", ""),
                expected_tool_calls=tc.get("expected_tool_calls", []),
                expected_output=tc.get("expected_output", {}),
                max_allowed_latency_ms=tc.get("max_allowed_latency_ms", 3500),
                evaluation_criteria=tc.get("evaluation_criteria", {})
            )
            db.add(test_case)
            imported_count += 1

        db.commit()
        return imported_count
