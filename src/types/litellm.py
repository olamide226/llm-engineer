from typing import List, Optional

from pydantic import BaseModel


class Function(BaseModel):
    arguments: str
    name: str


class ChatCompletionMessageToolCall(BaseModel):
    function: Function
    id: str
    type: str


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class Message(BaseModel):
    content: Optional[str]
    role: str
    tool_calls: Optional[List[ChatCompletionMessageToolCall]]


class Choices(BaseModel):
    finish_reason: str
    index: int
    message: Message


class ModelResponse(BaseModel):
    id: str
    choices: List[Choices]
    created: int
    model: str
    object: str
    system_fingerprint: Optional[str]
    usage: Usage


# Example instantiation:
ModelResponse.__doc__ = """
model_response = ModelResponse(
    id='chatcmpl-AKu0igpcKjqXzcHSv0e3MKqUf2z6L',
    choices=[
        Choices(
            finish_reason='tool_calls',
            index=0,
            message=Message(
                content=None,
                role='assistant',
                tool_calls=[
                    ChatCompletionMessageToolCall(
                        function=Function(
                            arguments='{"order_id":"1000"}',
                            name='get_delivery_date'
                        ),
                        id='call_p1b6vxjDKZblxhqwdZTAKluc',
                        type='function'
                    )
                ]
            )
        )
    ],
    created=1729545228,
    model='gpt-4o-mini-2024-07-18',
    object='chat.completion',
    system_fingerprint='fp_482c22a7bc',
    usage=Usage(completion_tokens=17, prompt_tokens=137, total_tokens=154)
)
print(model_response)
"""


class ParameterProperty(BaseModel):
    type: str
    description: str
    enum: Optional[List[str]] = None


class Parameters(BaseModel):
    type: str
    properties: dict  # Use a dictionary to allow for dynamic property names
    required: List[str] = []


class CacheControl(BaseModel):
    type: str  # Specifies the type of cache control (e.g., "ephemeral")


class ToolFunction(BaseModel):
    name: str
    description: str
    parameters: Parameters
    cache_control: Optional[CacheControl] = None


class Tool(BaseModel):
    type: str
    function: ToolFunction


class ToolsList(BaseModel):
    tools: List[Tool]


ToolsList.__doc__ = """
# Example instantiation of the tools data
tools_data = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                    },
                },
                "required": ["location"],
            },
            "cache_control": {"type": "ephemeral"},
        },
    }
]

# Example usage of the schema
tools_list = ToolsList(tools=tools_data)

print(tools_list.model_dump_json(indent=4))
"""

__all__ = ["ModelResponse", "ToolsList"]
