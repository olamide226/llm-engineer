from pydantic import BaseModel


def singleton(cls: type["GlobalState"]):
    instances = {}

    def get_instance(*args, **kwargs) -> "GlobalState":
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


class TokenTracking(BaseModel):
    input: int = 0
    output: int = 0


@singleton
class GlobalState(BaseModel):
    # Token tracking variables
    main_model_tokens: TokenTracking = TokenTracking()
    tool_checker_tokens: TokenTracking = TokenTracking()
    code_editor_tokens: TokenTracking = TokenTracking()
    code_execution_tokens: TokenTracking = TokenTracking()

    # Conversation memory
    conversation_history: list[str] = []

    # File contents
    file_contents: dict[str, str] = {}

    # Code editor memory
    code_editor_memory: list[str] = []

    # Files in code editor context
    code_editor_files: set[str] = set()

    # Automode flag
    automode: bool = False

    # Running processes
    running_processes: dict[int, object] = {}

    # Constants
    CONTINUATION_EXIT_PHRASE: str = "AUTOMODE_COMPLETE"
    MAX_CONTINUATION_ITERATIONS: int = 25
    MAX_CONTEXT_TOKENS: int = 200000

    # Models
    MAINMODEL: str = "claude-3-5-sonnet-20240620"
    TOOLCHECKERMODEL: str = "claude-3-5-sonnet-20240620"
    CODEEDITORMODEL: str = "claude-3-5-sonnet-20240620"
    CODEEXECUTIONMODEL: str = "claude-3-5-sonnet-20240620"


global_state = GlobalState()

__all__ = ["global_state"]
