from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, generate_uuid


class EvaluationRun(Base, TimestampMixin):
    __tablename__ = "evaluation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), index=True, nullable=False)
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), index=True, nullable=False)
    
    agent_version_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    dataset_version_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Status: PENDING, QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED
    status: Mapped[str] = mapped_column(String(50), default="PENDING", index=True, nullable=False)
    
    # Progress & Counts
    total_test_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_test_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passed_test_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_test_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Aggregated metrics (e.g. task_success_rate, tool_selection_f1, avg_latency, total_cost, etc.)
    aggregate_metrics: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    
    # Immutable Snapshots
    agent_snapshot: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    dataset_snapshot: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    
    # Concurrency & Config
    concurrency_limit: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    selected_evaluators: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    
    # Status & Error details
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="evaluation_runs")
    agent = relationship("Agent", back_populates="evaluation_runs")
    dataset = relationship("Dataset", back_populates="evaluation_runs")
    test_results = relationship("TestResult", back_populates="evaluation_run", cascade="all, delete-orphan", order_by="TestResult.created_at")
    traces = relationship("ExecutionTrace", back_populates="evaluation_run", cascade="all, delete-orphan")


class TestResult(Base, TimestampMixin):
    __tablename__ = "test_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    evaluation_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("evaluation_runs.id", ondelete="CASCADE"), index=True, nullable=False)
    test_case_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    test_case_identifier: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "TC-001"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Result: PASS, FAIL, ERROR
    status: Mapped[str] = mapped_column(String(20), default="FAIL", index=True, nullable=False)
    
    duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    actual_response: Mapped[str] = mapped_column(Text, default="", nullable=False)
    actual_tool_calls: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    
    # Structured outcomes from all executed evaluators
    metrics: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    
    # Categorization of any failure (e.g., "tool_selection_mismatch", "json_syntax_error", "timeout", "safety_violation")
    failure_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    failure_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trace_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    evaluation_run = relationship("EvaluationRun", back_populates="test_results")
    trace = relationship("ExecutionTrace", back_populates="test_result", uselist=False, cascade="all, delete-orphan")


class ExecutionTrace(Base, TimestampMixin):
    __tablename__ = "execution_traces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    evaluation_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("evaluation_runs.id", ondelete="CASCADE"), index=True, nullable=False)
    test_result_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("test_results.id", ondelete="CASCADE"), index=True, nullable=True)
    test_case_identifier: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Steps list: [{"timestamp": "...", "type": "USER_INPUT"|"AGENT_REASONING"|"TOOL_CALL"|"TOOL_RESULT"|"FINAL_OUTPUT", "content": ...}]
    steps: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    redacted_secrets_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    evaluation_run = relationship("EvaluationRun", back_populates="traces")
    test_result = relationship("TestResult", back_populates="trace")
