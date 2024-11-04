import os
from typing import Any, Dict, List, Optional

from openai import AuthenticationError
from src.console import SIMPLE, console

from src.providers.llm_provider_base import LLMProvider
from src.config import config
import litellm


class LiteLLMProvider(LLMProvider):
    def __init__(self):
        os.environ["OPENAI_API_BASE"] = config.open_api_base_url
        # litellm.set_verbose = True

    async def create_message(
        self,
        model: str,
        system: str,
        messages: List[Dict[str, Any]],
        max_tokens: int = 8192,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Dict[str, str]] = None,
    ) -> Any:
        
        try:
            return await litellm.acompletion(
            model=model,
            messages=[{"role": "system", "content": system}] + messages,
            max_tokens=max_tokens,
            tools=tools,
            tool_choice=tool_choice,
            extra_headers={
                "Authorization": "Bearer " + config.custom_api_token,
            },
            api_key="api-key",
            )
        except AuthenticationError as exc:
            if 401 == exc.status_code and "expired" in exc.message:
                from src.tools.utils import refresh_token
                console.print(SIMPLE, "Refreshing token...")
                await refresh_token()

                return await self.create_message(
                    model=model,
                    system=system,
                    messages=messages,
                    max_tokens=max_tokens,
                    tools=tools,
                    tool_choice=tool_choice,
                )
            raise exc

