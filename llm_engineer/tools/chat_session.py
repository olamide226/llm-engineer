import datetime
import json

from llm_engineer.global_state import global_state


def save_chat():
    """Save the conversation history to a markdown file."""
    # Generate filename
    now = datetime.datetime.now()
    filename = f"Chat_{now.strftime('%H%M')}.md"

    # Format conversation history
    formatted_chat = "# LLM Engineer Chat Log\n\n"
    for message in global_state.conversation_history:
        if message["role"] == "user":
            formatted_chat += f"## User\n\n{message['content']}\n\n"
        elif message["role"] == "assistant":
            if isinstance(message["content"], str):
                formatted_chat += f"## CodeMason\n\n{message['content']}\n\n"
            elif isinstance(message["content"], list):
                for content in message["content"]:
                    if content["type"] == "tool_use":
                        formatted_chat += f"### Tool Use: {content['name']}\n\n```json\n{json.dumps(content['input'], indent=2)}\n```\n\n"
                    elif content["type"] == "text":
                        formatted_chat += f"## CodeMason\n\n{content['text']}\n\n"
        elif message["role"] == "user" and isinstance(message["content"], list):
            for content in message["content"]:
                if content["type"] == "tool_result":
                    formatted_chat += f"### Tool Result\n\n```\n{content['content']}\n```\n\n"

    # Save to file
    with open(filename, "w", encoding="utf-8") as file:
        file.write(formatted_chat)

    return filename
