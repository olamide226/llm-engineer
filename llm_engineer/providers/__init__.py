from llm_engineer.providers.anthropic import AnthropicProvider
from llm_engineer.providers.litellm import LiteLLMProvider
from llm_engineer.providers.llm_provider_base import LLMProvider

_provider_cache: dict[str, LLMProvider] = {}


def get_llm_provider(provider_name: str):
    """
    Retrieve an instance of an LLMProvider based on the given provider name.

    This function checks if the provider is already cached. If not, it creates
    a new instance of the provider based on the provider name and any additional
    keyword arguments.

    Args:
        provider_name (str): The name of the LLM provider to retrieve.
        **kwargs: Additional keyword arguments required for certain providers.

    Returns:
        LLMProvider: An instance of the requested LLM provider.

    Raises:
        ValueError: If the provider name is unknown or if required arguments
                    for certain providers are not provided.

    Supported Providers:
        - "anthropic": Returns an instance of AnthropicProvider.
        - "litellm": Returns an instance of LiteLLMProvider.
        - "custom": Returns an instance of CustomModelProvider with a custom client.
        - "custom_endpoint": Returns an instance of CustomEndpointProvider with the
                             specified endpoint URL.
    """
    # TODO: Move to config validation at the start of the program
    if provider_name in _provider_cache:
        return _provider_cache[provider_name]

    if provider_name == "anthropic":
        provider = AnthropicProvider()
    elif provider_name == "custom":
        provider = LiteLLMProvider()
    elif provider_name == "openai":
        provider = LiteLLMProvider()
    elif provider_name == "ollama":
        provider = LiteLLMProvider()
    elif provider_name == "grok":
        provider = GrokProvider()
    else:
        raise ValueError(f"Unknown provider: {provider_name}")

    _provider_cache[provider_name] = provider
    return provider


__all__ = [
    "get_llm_provider",
    "LLMProvider",
]
