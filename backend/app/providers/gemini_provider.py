import time
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types
from app.config import settings
from app.core.errors import ProviderException
from app.providers.base import BaseLLMProvider, ProviderResponse, ProviderToolCall, ProviderUsage


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash"):
        effective_key = api_key or settings.GEMINI_API_KEY
        super().__init__(api_key=effective_key, model_name=model_name or "gemini-1.5-flash")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def _ensure_client(self):
        if not self.api_key or not self.client:
            raise ProviderException(
                "gemini",
                "Google Gemini API Key is missing. Please configure GEMINI_API_KEY in your environment, or provide your key in Provider Settings."
            )

    async def test_connection(self) -> Dict[str, Any]:
        self._ensure_client()
        start = time.time()
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents="ping",
                config=types.GenerateContentConfig(max_output_tokens=5)
            )
            duration_ms = int((time.time() - start) * 1000)
            return {
                "success": True,
                "latency_ms": duration_ms,
                "message": f"Successfully connected to Gemini {self.model_name}",
                "model": self.model_name
            }
        except Exception as e:
            raise ProviderException("gemini", str(e))

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
        
        # Build configuration
        config_kwargs: Dict[str, Any] = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        if system_prompt:
            config_kwargs["system_instruction"] = system_prompt
            
        if json_schema:
            config_kwargs["response_mime_type"] = "application/json"

        # Format tools if provided
        if tools:
            declarations = []
            for t in tools:
                raw_params = t.get("parameters", {})
                props = {}
                for pk, pv in raw_params.items():
                    if isinstance(pv, dict):
                        props[pk] = pv
                    else:
                        props[pk] = {"type": "STRING"}
                declarations.append({
                    "name": t.get("name"),
                    "description": t.get("description", ""),
                    "parameters": {
                        "type": "OBJECT",
                        "properties": props,
                        "required": list(raw_params.keys())
                    }
                })
            config_kwargs["tools"] = [{"function_declarations": declarations}]

        config = types.GenerateContentConfig(**config_kwargs)

        start = time.time()
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            duration_ms = int((time.time() - start) * 1000)
        except Exception as e:
            raise ProviderException("gemini", str(e))

        text_content = ""
        tool_calls: List[ProviderToolCall] = []

        if response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, "text") and part.text:
                        text_content += part.text
                    if hasattr(part, "function_call") and part.function_call:
                        fc = part.function_call
                        args = dict(fc.args) if hasattr(fc, "args") and fc.args else {}
                        tool_calls.append(ProviderToolCall(
                            tool_name=fc.name,
                            arguments=args,
                            call_id=getattr(fc, "id", None)
                        ))

        # Usage extraction
        usage = ProviderUsage()
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            meta = response.usage_metadata
            usage.input_tokens = getattr(meta, "prompt_token_count", 0) or 0
            usage.output_tokens = getattr(meta, "candidates_token_count", 0) or 0
            usage.total_tokens = getattr(meta, "total_token_count", 0) or 0

        return ProviderResponse(
            text=text_content,
            tool_calls=tool_calls,
            usage=usage,
            model_name=self.model_name,
            provider_name="gemini",
            duration_ms=duration_ms
        )
