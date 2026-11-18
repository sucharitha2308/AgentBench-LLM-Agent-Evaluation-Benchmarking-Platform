from typing import Any, Dict, List, Optional
from sqlalchemy import Float, ForeignKey, Integer, String, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, generate_uuid


class Agent(Base, TimestampMixin):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Agent architecture: direct_llm, langgraph, http
    agent_type: Mapped[str] = mapped_column(String(50), default="direct_llm", nullable=False)
    
    # Provider: openai, gemini, mock
    provider: Mapped[str] = mapped_column(String(50), default="mock", nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), default="mock-agent", nullable=False)
    
    # Configuration
    system_prompt: Mapped[str] = mapped_column(Text, default="", nullable=False)
    temperature: Mapped[float] = mapped_column(Float, default=0.2, nullable=False)
    max_output_tokens: Mapped[int] = mapped_column(Integer, default=2048, nullable=False)
    output_format: Mapped[str] = mapped_column(String(50), default="text", nullable=False)  # "text" or "json"
    
    # Tools configured for this agent (e.g. ["get_order", "check_refund_eligibility", "search_products", "get_weather"])
    tools: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    
    # Optional endpoint for HTTP agents
    http_endpoint: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    
    # Whether this is a sample/demo agent
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="agents")
    versions = relationship("AgentVersion", back_populates="agent", cascade="all, delete-orphan", order_by="desc(AgentVersion.version_number)")
    evaluation_runs = relationship("EvaluationRun", back_populates="agent", cascade="all, delete-orphan")


class AgentVersion(Base, TimestampMixin):
    __tablename__ = "agent_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), index=True, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    commit_message: Mapped[str] = mapped_column(String(255), default="Update agent configuration", nullable=False)
    configuration_snapshot: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    agent = relationship("Agent", back_populates="versions")
