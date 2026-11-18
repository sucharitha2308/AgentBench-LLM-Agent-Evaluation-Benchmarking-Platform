from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ProviderToolCall(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    call_id: Optional[str] = None


class ProviderUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class ProviderResponse(BaseModel):
    text: str = ""
    tool_calls: List[ProviderToolCall] = []
    usage: ProviderUsage = ProviderUsage()
    model_name: str = ""
    provider_name: str = ""
    duration_ms: int = 0
    raw_response: Optional[Dict[str, Any]] = None


class BaseLLMProvider(ABC):
    def __init__(self, api_key: Optional[str] = None, model_name: str = ""):
        self.api_key = api_key
        self.model_name = model_name

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
        json_schema: Optional[Dict[str, Any]] = None
    ) -> ProviderResponse:
        """Execute model generation with optional tools or structured schema."""
        pass

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Verify API key validity and model responsiveness."""
        pass
