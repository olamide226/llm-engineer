from typing import List

from src.tools.tool_schemas.anthropic_tool_schema import AnthropicTool
from src.types.litellm import ToolsList


# Transform JSON data to match the litellm Pydantic model
def transform_tools_to_litellm(tools: List[AnthropicTool]) -> ToolsList:
    tools_data = [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": tool.input_schema["type"],
                    "properties": {
                        key: {"type": value["type"], "description": value["description"]}
                        for key, value in tool.input_schema["properties"].items()
                    },
                    "required": tool.input_schema.get("required", []),
                },
            },
        }
        for tool in tools
    ]

    return ToolsList(tools=tools_data)
