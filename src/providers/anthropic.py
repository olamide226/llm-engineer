"""Anthropic provider"""

import os
import asyncio
from typing import Any, Dict, List, Optional

from anthropic import AsyncAnthropic, APIError, APIStatusError

from dotenv import load_dotenv

from .llm_provider_base import LLMProvider
from src.console import Panel, console

# Load environment variables from .env file
load_dotenv()

# to maintain backward compatibility, we will maintain this provider even though it can be handle thru litellm provider
class AnthropicProvider(LLMProvider):
    def __init__(self):
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        self.client = AsyncAnthropic()

    async def create_message(self, model: str, max_tokens: int, system: str, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, tool_choice: Optional[Dict[str, str]] = None) -> Any:
        try:
            return await self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            extra_headers={"anthropic-beta": "max-tokens-3-5-sonnet-2024-07-15"}
            )
        except APIStatusError as exc:
            if exc.status_code == 429:
                console.print(
                    Panel(
                        "Rate limit exceeded. Retrying after a short delay...",
                        title="API Error",
                        style="bold yellow",
                    )
                )
                await asyncio.sleep(5)
                return await self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    system=system,
                    messages=messages,
                    tools=tools,
                    tool_choice=tool_choice,
                    extra_headers={"anthropic-beta": "max-tokens-3-5-sonnet-2024-07-15"}
                )
            else:
                raise exc
        except APIError as exc:
            console.print(Panel(f"API Error: {str(exc)}", title="API Error", style="bold red"))
            raise exc
            
        except Exception:
            raise
