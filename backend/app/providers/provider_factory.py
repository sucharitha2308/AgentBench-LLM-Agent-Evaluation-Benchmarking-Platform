from typing import Optional
from app.core.errors import BadRequestException
from app.providers.base import BaseLLMProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.mock_provider import MockProvider


class ProviderFactory:
    @staticmethod
    def get_provider(
        provider_name: str,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> BaseLLMProvider:
        prov = provider_name.lower().strip()
        
        if prov == "openai":
            return OpenAIProvider(api_key=api_key, model_name=model_name or "gpt-4o-mini")
        elif prov == "gemini":
            return GeminiProvider(api_key=api_key, model_name=model_name or "gemini-1.5-flash")
        elif prov in ["mock", "demo", "simulated"]:
            return MockProvider(api_key=api_key, model_name=model_name or "mock-agent")
        else:
            raise BadRequestException(f"Unsupported provider: '{provider_name}'. Supported providers: openai, gemini, mock.")
