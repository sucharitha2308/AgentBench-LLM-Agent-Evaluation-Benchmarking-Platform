from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TestCaseBase(BaseModel):
    test_case_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    user_input: str = Field(..., min_length=1)
    difficulty_level: str = Field(default="medium", pattern="^(easy|medium|hard)$")
    tags: List[str] = Field(default_factory=list)
    expected_behavior: str = ""
    expected_tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    expected_output: Dict[str, Any] = Field(default_factory=dict)
    max_allowed_latency_ms: int = Field(default=3500, ge=100)
    evaluation_criteria: Dict[str, Any] = Field(default_factory=dict)


class TestCaseCreate(TestCaseBase):
    pass


class TestCaseUpdate(BaseModel):
    test_case_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    user_input: Optional[str] = None
    difficulty_level: Optional[str] = Field(None, pattern="^(easy|medium|hard)$")
    tags: Optional[List[str]] = None
    expected_behavior: Optional[str] = None
    expected_tool_calls: Optional[List[Dict[str, Any]]] = None
    expected_output: Optional[Dict[str, Any]] = None
    max_allowed_latency_ms: Optional[int] = None
    evaluation_criteria: Optional[Dict[str, Any]] = None


class TestCaseResponse(TestCaseBase):
    id: str
    dataset_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DatasetBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    domain: str = "customer_support"


class DatasetCreate(DatasetBase):
    test_cases: Optional[List[TestCaseCreate]] = None


class DatasetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None


class DatasetVersionResponse(BaseModel):
    id: str
    dataset_id: str
    version_number: int
    test_case_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class DatasetResponse(DatasetBase):
    id: str
    user_id: str
    is_sample: bool
    test_case_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DatasetExportResponse(BaseModel):
    dataset_name: str
    description: Optional[str]
    domain: str
    version: str
    exported_at: str
    test_cases: List[Dict[str, Any]]
