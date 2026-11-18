from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    agent_type: str = Field(default="direct_llm", pattern="^(direct_llm|langgraph|http)$")
    provider: str = Field(default="mock", pattern="^(openai|gemini|mock)$")
    model_name: str = "mock-agent"
    system_prompt: str = ""
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_output_tokens: int = Field(default=2048, ge=64, le=32768)
    output_format: str = Field(default="text", pattern="^(text|json)$")
    tools: List[Dict[str, Any]] = Field(default_factory=list)
    http_endpoint: Optional[str] = None


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    agent_type: Optional[str] = Field(None, pattern="^(direct_llm|langgraph|http)$")
    provider: Optional[str] = Field(None, pattern="^(openai|gemini|mock)$")
    model_name: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_output_tokens: Optional[int] = Field(None, ge=64, le=32768)
    output_format: Optional[str] = Field(None, pattern="^(text|json)$")
    tools: Optional[List[Dict[str, Any]]] = None
    http_endpoint: Optional[str] = None


class AgentVersionResponse(BaseModel):
    id: str
    agent_id: str
    version_number: int
    commit_message: str
    configuration_snapshot: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class AgentResponse(AgentBase):
    id: str
    user_id: str
    is_sample: bool
    created_at: datetime
    updated_at: datetime
    versions_count: Optional[int] = 0

    class Config:
        from_attributes = True


class ConnectionTestRequest(BaseModel):
    provider: str
    model_name: str
    api_key: Optional[str] = None


class ConnectionTestResponse(BaseModel):
    success: bool
    provider: str
    model_name: str
    message: str
    latency_ms: int
    raw_response: Optional[str] = None
