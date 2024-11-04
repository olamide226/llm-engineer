"""
Global state management for the CodeMason Engineer Chat application.

This module defines the global state of the application, including token tracking,
conversation history, file contents, and various configuration settings. It uses
a singleton pattern to ensure a single instance of the global state is maintained
throughout the application's lifecycle.
"""

from typing import Any, Dict, List, Set

from pydantic import BaseModel


def singleton(cls: type["GlobalState"]):
    """
    Decorator to implement the singleton pattern for the GlobalState class.

    Args:
        cls (type["GlobalState"]): The class to be decorated.

    Returns:
        Callable: A function that returns the single instance of the class.
    """
    instances: Dict[type["GlobalState"], "GlobalState"] = {}

    def get_instance(*args: Any, **kwargs: Any) -> "GlobalState":
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


class TokenTracking(BaseModel):
    """
    Model for tracking input and output tokens for various components.
    """

    input: int = 0
    output: int = 0


@singleton
class GlobalState(BaseModel):
    """
    Singleton class representing the global state of the application.

    This class manages various aspects of the application's state, including
    token tracking, conversation history, file contents, and configuration settings.
    """

    # Token tracking variables
    main_model_tokens: TokenTracking = TokenTracking()
    tool_checker_tokens: TokenTracking = TokenTracking()
    code_editor_tokens: TokenTracking = TokenTracking()
    code_execution_tokens: TokenTracking = TokenTracking()

    # Conversation memory
    conversation_history: List[Dict[str, str]] = []

    # File contents
    file_contents: Dict[str, str] = {}

    # Code editor memory
    code_editor_memory: List[str] = []

    # Files in code editor context
    code_editor_files: Set[str] = set()

    # Autonomous mode flag
    autonomous_mode: bool = False

    # Running processes
    running_processes: Dict[int, Any] = {}

    # Constants
    CONTINUATION_EXIT_PHRASE: str = "AUTOMODE_COMPLETE"  # Phrase to exit autonomous mode
    MAX_CONTINUATION_ITERATIONS: int = 25  # Maximum number of iterations in autonomous mode
    MAX_CONTEXT_TOKENS: int = 200000  # Maximum number of tokens for context

    # LLM provider configuration (options: "anthropic", "litellm", "custom")
    LLM_PROVIDER: str = "custom"

    # Models
    MAIN_MODEL: str = "gpt-4o"
    TOOL_CHECKER_MODEL: str = "gpt-4o"
    CODE_EDITOR_MODEL: str = "gpt-4o"
    CODE_EXECUTION_MODEL: str = "gpt-4o"



global_state = GlobalState()

__all__ = ["global_state"]
