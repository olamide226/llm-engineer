import httpx
from typing import Any, Dict, List, Optional
from .llm_provider_base import LLMProvider

class CustomEndpointProvider(LLMProvider):
    def __init__(self, endpoint_url: str):
        self.endpoint_url = endpoint_url
        self.client = httpx.AsyncClient()

    async def create_message(self, model: str, max_tokens: int, system: str, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, tool_choice: Optional[Dict[str, str]] = None) -> Any:
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
            "tools": tools,
            "tool_choice": tool_choice
        }
        try:
            response = await self.client.post(self.endpoint_url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise Exception(f"HTTP error occurred: {exc}") from exc
        except httpx.RequestError as exc:
            raise Exception(f"An error occurred while making the request: {exc}") from exc