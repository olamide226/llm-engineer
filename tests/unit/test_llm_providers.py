import pytest
from unittest.mock import Mock, patch, AsyncMock
from llm_engineer.providers import (
    AnthropicProvider,
    LiteLLMProvider,
    CustomEndpointProvider,
    get_llm_provider,
)

@pytest.mark.asyncio
async def test_get_llm_provider():
    assert isinstance(await get_llm_provider("anthropic"), AnthropicProvider)
    assert isinstance(await get_llm_provider("litellm"), LiteLLMProvider)
    with pytest.raises(ValueError):
        await get_llm_provider("unknown_provider")

@patch('llm_engineer.models.llm_providers.AnthropicProvider.client', new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_anthropic_provider(mock_client):
    mock_client.messages.create.return_value = Mock(content=[Mock(text="Test response")])

    provider = AnthropicProvider()
    response = await provider.create_message(
        model="test-model",
        max_tokens=100,
        system="Test system",
        messages=[{"role": "user", "content": "Test message"}]
    )

    mock_client.messages.create.assert_called_once()
    assert response.content[0].text == "Test response"

@patch('llm_engineer.models.llm_providers.LiteLLMProvider.litellm', new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_litellm_provider(mock_litellm):
    mock_litellm.acompletion.return_value = Mock(choices=[Mock(message={"content": "Test response"})])

    provider = LiteLLMProvider()
    response = await provider.create_message(
        model="test-model",
        max_tokens=100,
        system="Test system",
        messages=[{"role": "user", "content": "Test message"}]
    )

    mock_litellm.acompletion.assert_called_once()
    assert response.choices[0].message["content"] == "Test response"

@patch('llm_engineer.models.llm_providers.httpx.AsyncClient')
@pytest.mark.asyncio
async def test_custom_endpoint_provider(mock_httpx):
    mock_client = AsyncMock()
    mock_httpx.return_value = mock_client
    mock_client.post.return_value.json.return_value = {"result": "Test response"}

    provider = CustomEndpointProvider("http://test-endpoint")
    response = await provider.create_message(
        model="test-model",
        max_tokens=100,
        system="Test system",
        messages=[{"role": "user", "content": "Test message"}]
    )

    mock_client.post.assert_called_once_with(
        "http://test-endpoint",
        json={
            "model": "test-model",
            "max_tokens": 100,
            "system": "Test system",
            "messages": [{"role": "user", "content": "Test message"}],
            "tools": None,
            "tool_choice": None
        }
    )
    assert response == {"result": "Test response"}
