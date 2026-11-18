from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, generate_uuid


class Dataset(Base, TimestampMixin):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    domain: Mapped[str] = mapped_column(String(100), default="customer_support", nullable=False)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="datasets")
    test_cases = relationship("TestCase", back_populates="dataset", cascade="all, delete-orphan", order_by="TestCase.test_case_id")
    versions = relationship("DatasetVersion", back_populates="dataset", cascade="all, delete-orphan", order_by="desc(DatasetVersion.version_number)")
    evaluation_runs = relationship("EvaluationRun", back_populates="dataset", cascade="all, delete-orphan")


class DatasetVersion(Base, TimestampMixin):
    __tablename__ = "dataset_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), index=True, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    test_case_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    snapshot: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False)

    dataset = relationship("Dataset", back_populates="versions")


class TestCase(Base, TimestampMixin):
    __tablename__ = "test_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), index=True, nullable=False)
    test_case_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # e.g., "TC-001"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Test definition
    user_input: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty_level: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)  # easy, medium, hard
    tags: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    
    # Expectations
    expected_behavior: Mapped[str] = mapped_column(Text, default="", nullable=False)
    expected_tool_calls: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    expected_output: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    max_allowed_latency_ms: Mapped[int] = mapped_column(Integer, default=4000, nullable=False)
    evaluation_criteria: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    dataset = relationship("Dataset", back_populates="test_cases")
