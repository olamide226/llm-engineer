from .llm_provider_base import LLMProvider
from .anthropic import AnthropicProvider
from .litellm import LiteLLMProvider
from .custom import CustomEndpointProvider


_provider_cache: dict[str, LLMProvider] = {}

def get_llm_provider(provider_name: str, **kwargs) -> LLMProvider:
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
    if provider_name in _provider_cache:
        return _provider_cache[provider_name]

    if provider_name == "anthropic":
        provider = AnthropicProvider()
    elif provider_name == "litellm":
        provider = LiteLLMProvider()
    elif provider_name == "custom_endpoint":
        endpoint_url = kwargs.get("endpoint_url")
        if not endpoint_url:
            raise ValueError("endpoint_url is required for custom_endpoint provider")
        provider = CustomEndpointProvider(endpoint_url)
    else:
        raise ValueError(f"Unknown provider: {provider_name}")

    _provider_cache[provider_name] = provider
    return provider

__all__ = ["get_llm_provider", "LLMProvider", ]