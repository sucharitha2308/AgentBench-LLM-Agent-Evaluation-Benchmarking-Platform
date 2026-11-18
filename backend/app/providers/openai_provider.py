import json
import time
from typing import Any, Dict, List, Optional
from openai import AsyncOpenAI, APIError, AuthenticationError
from app.config import settings
from app.core.errors import ProviderException
from app.providers.base import BaseLLMProvider, ProviderResponse, ProviderToolCall, ProviderUsage


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gpt-4o-mini"):
        effective_key = api_key or settings.OPENAI_API_KEY
        super().__init__(api_key=effective_key, model_name=model_name or "gpt-4o-mini")
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
        else:
            self.client = None

    def _ensure_client(self):
        if not self.api_key or not self.client:
            raise ProviderException(
                "openai",
                "OpenAI API Key is missing. Please configure OPENAI_API_KEY in your environment, or provide your key in Provider Settings."
            )

    async def test_connection(self) -> Dict[str, Any]:
        self._ensure_client()
        start = time.time()
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5
            )
            duration_ms = int((time.time() - start) * 1000)
            return {
                "success": True,
                "latency_ms": duration_ms,
                "message": f"Successfully connected to OpenAI {self.model_name}",
                "model": response.model
            }
        except AuthenticationError:
            raise ProviderException("openai", "Invalid OpenAI API Key. Please verify your credentials.")
        except Exception as e:
            raise ProviderException("openai", str(e))

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
        json_schema: Optional[Dict[str, Any]] = None
    ) -> ProviderResponse:
        self._ensure_client()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        formatted_tools = None
        if tools:
            formatted_tools = []
            for t in tools:
                tool_dict = {
                    "type": "function",
                    "function": {
                        "name": t.get("name"),
                        "description": t.get("description", ""),
                        "parameters": {
                            "type": "object",
                            "properties": t.get("parameters", {}),
                            "required": list(t.get("parameters", {}).keys())
                        }
                    }
                }
                formatted_tools.append(tool_dict)

        kwargs: Dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if formatted_tools:
            kwargs["tools"] = formatted_tools
        if json_schema:
            kwargs["response_format"] = {"type": "json_object"}

        start = time.time()
        try:
            response = await self.client.chat.completions.create(**kwargs)
            duration_ms = int((time.time() - start) * 1000)
        except Exception as e:
            raise ProviderException("openai", str(e))

        choice = response.choices[0]
        text_content = choice.message.content or ""
        tool_calls: List[ProviderToolCall] = []

        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = {"raw_arguments": tc.function.arguments}
                tool_calls.append(ProviderToolCall(
                    tool_name=tc.function.name,
                    arguments=args,
                    call_id=tc.id
                ))

        usage = ProviderUsage(
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
            total_tokens=response.usage.total_tokens if response.usage else 0
        )

        return ProviderResponse(
            text=text_content,
            tool_calls=tool_calls,
            usage=usage,
            model_name=response.model or self.model_name,
            provider_name="openai",
            duration_ms=duration_ms
        )
