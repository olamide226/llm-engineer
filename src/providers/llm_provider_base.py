from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    """
    @abstractmethod
    async def create_message(self, model: str, max_tokens: int, system: str, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, tool_choice: Optional[Dict[str, str]] = None) -> Any:
        """
        Asynchronously creates a message using the specified model and parameters.

        Args:
            model (str): The name of the model to use for message creation.
            max_tokens (int): The maximum number of tokens allowed in the generated message.
            system (str): The system prompt or context for the message.
            messages (List[Dict[str, Any]]): A list of message dictionaries containing the conversation history.
            tools (Optional[List[Dict[str, Any]]], optional): A list of tool dictionaries that can be used in message creation. Defaults to None.
            tool_choice (Optional[Dict[str, str]], optional): A dictionary specifying the chosen tool and its parameters. Defaults to None.

        Returns:
            Any: The generated message or result from the model.
        """