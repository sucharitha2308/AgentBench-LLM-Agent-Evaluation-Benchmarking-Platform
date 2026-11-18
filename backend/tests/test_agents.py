import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.providers.openai_provider import OpenAIProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.mock_provider import MockProvider
from app.utils.redaction import redact_sensitive_data, redact_string
from app.core.errors import ProviderException


def test_agent_registration(client: TestClient, auth_headers: dict):
    """Scenario 4: Agent Registration & Configuration Checkpoints"""
    payload = {
        "name": "Customer Care Specialist",
        "description": "Handles returns and exchanges",
        "agent_type": "direct_llm",
        "provider": "mock",
        "model_name": "mock-agent",
        "system_prompt": "You are a customer support agent.",
        "temperature": 0.3,
        "max_output_tokens": 1024,
        "output_format": "text",
        "tools": [{"name": "get_order", "description": "Lookup order"}]
    }
    response = client.post("/api/v1/agents", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Customer Care Specialist"
    agent_id = data["id"]

    # Verify version 1 was created
    versions_res = client.get(f"/api/v1/agents/{agent_id}/versions", headers=auth_headers)
    assert versions_res.status_code == 200
    versions = versions_res.json()
    assert len(versions) == 1
    assert versions[0]["version_number"] == 1


@pytest.mark.asyncio
async def test_openai_adapter_mocked():
    """Scenario 7: OpenAI Adapter Normalization (Mocked API call)"""
    provider = OpenAIProvider(api_key="sk-testmockedkey12345678901234567890", model_name="gpt-4o-mini")
    
    # Mock AsyncOpenAI client response
    mock_choice = MagicMock()
    mock_choice.message.content = "Your package has shipped."
    mock_tc = MagicMock()
    mock_tc.id = "call_abc123"
    mock_tc.function.name = "get_order"
    mock_tc.function.arguments = '{"order_id": "ORD-1001"}'
    mock_choice.message.tool_calls = [mock_tc]

    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    mock_completion.model = "gpt-4o-mini-2024-07-18"
    mock_completion.usage.prompt_tokens = 45
    mock_completion.usage.completion_tokens = 22
    mock_completion.usage.total_tokens = 67

    with patch.object(provider.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_completion
        res = await provider.generate(
            prompt="Track ORD-1001",
            tools=[{"name": "get_order", "parameters": {"order_id": "string"}}]
        )

        assert res.provider_name == "openai"
        assert res.model_name == "gpt-4o-mini-2024-07-18"
        assert res.usage.total_tokens == 67
        assert len(res.tool_calls) == 1
        assert res.tool_calls[0].tool_name == "get_order"
        assert res.tool_calls[0].arguments == {"order_id": "ORD-1001"}


@pytest.mark.asyncio
async def test_gemini_adapter_mocked():
    """Scenario 8: Gemini Adapter Normalization (Mocked API call)"""
    provider = GeminiProvider(api_key="AIzaSyDummyKeyForTestingGeminiSDK12345", model_name="gemini-1.5-flash")

    # Mock candidate with function call
    mock_part = MagicMock()
    mock_part.text = "Checking order ORD-1001"
    mock_part.function_call.name = "get_order"
    mock_part.function_call.args = {"order_id": "ORD-1001"}
    mock_part.function_call.id = "fc_001"

    mock_candidate = MagicMock()
    mock_candidate.content.parts = [mock_part]

    mock_response = MagicMock()
    mock_response.candidates = [mock_candidate]
    mock_response.usage_metadata.prompt_token_count = 30
    mock_response.usage_metadata.candidates_token_count = 15
    mock_response.usage_metadata.total_token_count = 45

    with patch.object(provider.client.aio.models, "generate_content", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_response
        res = await provider.generate(
            prompt="Lookup status for ORD-1001",
            tools=[{"name": "get_order", "parameters": {"order_id": "string"}}]
        )

        assert res.provider_name == "gemini"
        assert len(res.tool_calls) == 1
        assert res.tool_calls[0].tool_name == "get_order"
        assert res.tool_calls[0].arguments == {"order_id": "ORD-1001"}
        assert res.usage.total_tokens == 45


def test_credential_redaction():
    """Scenario 17: Credential Redaction in traces and logs"""
    raw_text = "Connecting with key sk-abcdef1234567890abcdef1234567890 to backend"
    redacted = redact_string(raw_text)
    assert "sk-abcdef" not in redacted
    assert "[REDACTED_OPENAI_KEY]" in redacted

    gemini_text = "Google API key AIzaSyDUMMYKEYFORGEMINIVALIDATION12345 authorized"
    redacted_gemini = redact_string(gemini_text)
    assert "AIzaSy" not in redacted_gemini
    assert "[REDACTED_GEMINI_KEY]" in redacted_gemini

    nested_dict = {
        "user": "developer",
        "api_key": "super_secret_raw_key",
        "config": {
            "token": "bearer eyJhbGciOi...",
            "safe_val": "hello"
        }
    }
    cleaned = redact_sensitive_data(nested_dict)
    assert cleaned["api_key"] == "[REDACTED_SECRET]"
    assert cleaned["config"]["token"] == "[REDACTED_SECRET]"
    assert cleaned["config"]["safe_val"] == "hello"


@pytest.mark.asyncio
async def test_provider_failure_handling():
    """Scenario 19: Provider Failure Handling with Missing Key"""
    # Instantiating OpenAI provider with no key must raise clear ProviderException
    provider = OpenAIProvider(api_key="", model_name="gpt-4o-mini")
    with pytest.raises(ProviderException) as exc_info:
        await provider.generate("ping")
    assert "OpenAI API Key is missing" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_invalid_agent_response_handling():
    """Scenario 20: Resilience against corrupted or malformed agent outputs"""
    from app.agents.direct_llm_agent import DirectLLMAgent
    # Configure an agent with non-existent provider
    agent = DirectLLMAgent(config={"provider": "non_existent_provider"})
    result = await agent.execute("Hello")
    assert result.error is not None
    assert len(result.trace_steps) > 0
    # Trace must capture the error step cleanly
    assert any(s.get("event_type") == "ERROR" for s in result.trace_steps)
