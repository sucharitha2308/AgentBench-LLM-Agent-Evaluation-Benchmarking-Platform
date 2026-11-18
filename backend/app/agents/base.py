from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class AgentExecutionResult(BaseModel):
    final_response: str
    tool_calls: List[Dict[str, Any]] = []
    tool_results: List[Dict[str, Any]] = []
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    duration_ms: int = 0
    provider: str = ""
    model_name: str = ""
    error: Optional[str] = None
    trace_steps: List[Dict[str, Any]] = []


class BaseAgentAdapter(ABC):
    def __init__(self, config: Dict[str, Any], api_key: Optional[str] = None):
        self.config = config
        self.api_key = api_key

    @abstractmethod
    async def execute(self, user_input: str) -> AgentExecutionResult:
        """Execute agent on a user query and return normalized results."""
        pass
