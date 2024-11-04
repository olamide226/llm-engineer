from typing import Any, List, Optional

from pydantic import BaseModel


class ToolCallFunction(BaseModel):
    name: str
    arguments: str


class ToolCall(BaseModel):
    id: str
    type: str
    function: ToolCallFunction


class Message(BaseModel):
    role: str
    content: str
    refusal: Optional[str]
    tool_calls: Optional[List[ToolCall]]


class Choice(BaseModel):
    index: int
    message: Message
    logprobs: Any
    finish_reason: str


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class OpenAIResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[Choice]
    usage: Usage
    system_fingerprint: Any
