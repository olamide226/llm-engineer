from typing import Any, Dict, List, Optional

import litellm as liteLLM
from litellm import OpenAIError

from llm_engineer.console import Panel, console
from llm_engineer.providers.llm_provider_base import LLMProvider


class AnthropicProvider(LLMProvider):
    """
    Anthropic provider class for handling async completions and function calling with caching support.
    """

    async def create_message(
        self,
        model: str,
        system: str,
        messages: List[Dict[str, Any]],
        max_tokens: int = 8000,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Dict[str, str]] = None,
    ):
        """
        Asynchronously creates a message using the specified model and parameters.

        Args:
            model (str): The name of the model to use for message creation.
            max_tokens (int): The maximum number of tokens allowed in the generated message.
            system (str): The system prompt or context for the message.
            messages (List[Dict[str, Any]]): A list of message dictionaries containing the conversation history.
            tools (Optional[List[Dict[str, Any]]] optional): A list of tool dictionaries that can be used in message creation. Defaults to None.
            tool_choice (Optional[Dict[str, str]] optional): A dictionary specifying the chosen tool and its parameters. Defaults to None.

        Returns:
            Response: The generated message or result from the model.
        """
        try:
            response = await liteLLM.acompletion(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                tools=tools,
                tool_choice=tool_choice,
            )
            return response
        except OpenAIError as exc:
            console.print(
                Panel(
                    f"OpenAIError in AnthropicProvider: {str(exc)}",
                    title="API Error",
                    style="bold yellow",
                )
            )
            raise exc
        except Exception as exc:
            console.print(
                Panel(
                    f"Unexpected error in AnthropicProvider: {str(exc)}",
                    title="Error",
                    style="bold red",
                )
            )
            raise exc
