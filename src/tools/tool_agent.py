import asyncio
import json
import logging
from typing import Any

from src.console import Markdown, Panel, console, SIMPLE
from src.global_state import global_state
from src.providers import get_llm_provider, LLMProvider
from src.tools.file_system import (
    create_file,
    create_folder,
    execute_code,
    list_files,
    read_file,
    read_multiple_files,
    stop_process,
)
from src.tools.web_search import tavily_search
from src.tools.file_system import edit_and_apply
from src.tools.tool_schemas import TOOL_SCHEMA
from src.tools.utils import (
    display_token_usage,
    encode_image_to_base64,
    update_system_prompt,
)


async def send_to_ai_for_executing(code: str, execution_result: str):
    """Send the code execution details to the AI for analysis."""
    try:
        system_prompt = f"""
        You are an AI code execution agent. Your task is to analyze the provided code and its execution result from the 'code_execution_env' virtual environment, then provide a concise summary of what worked, what didn't work, and any important observations. Follow these steps:

        1. Review the code that was executed in the 'code_execution_env' virtual environment:
        {code}

        2. Analyze the execution result from the 'code_execution_env' virtual environment:
        {execution_result}

        3. Provide a brief summary of:
           - What parts of the code executed successfully in the virtual environment
           - Any errors or unexpected behavior encountered in the virtual environment
           - Potential improvements or fixes for issues, considering the isolated nature of the environment
           - Any important observations about the code's performance or output within the virtual environment
           - If the execution timed out, explain what this might mean (e.g., long-running process, infinite loop)

        Be concise and focus on the most important aspects of the code execution within the 'code_execution_env' virtual environment.

        IMPORTANT: PROVIDE ONLY YOUR ANALYSIS AND OBSERVATIONS. DO NOT INCLUDE ANY PREFACING STATEMENTS OR EXPLANATIONS OF YOUR ROLE.
        """

        llm_provider: LLMProvider = get_llm_provider(global_state.LLM_PROVIDER)
        response = await llm_provider.create_message(
            model=global_state.CODEEXECUTIONMODEL,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"Analyze this code execution from the 'code_execution_env' virtual environment:\n\nCode:\n{code}\n\nExecution Result:\n{execution_result}",
                }
            ],
            max_tokens=2000,
        )

        # Update token usage for code execution
        global_state.code_execution_tokens.input += response.usage.input_tokens
        global_state.code_execution_tokens.output += response.usage.output_tokens

        analysis = response.content[0].text

        return analysis

    except Exception as exc:
        console.print(f"Error in AI code execution analysis: {str(exc)}", style="bold red")
        return f"Error analyzing code execution from 'code_execution_env': {str(exc)}"


async def execute_tool(tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    """Execute the specified tool with the given input."""
    try:
        result = None
        is_error = False

        if tool_name == "create_folder":
            result = create_folder(tool_input["path"])
        elif tool_name == "create_file":
            result = create_file(tool_input["path"], tool_input.get("content", ""))
        elif tool_name == "edit_and_apply":
            result = await edit_and_apply(tool_input["path"], tool_input["instructions"], tool_input["project_context"])
        elif tool_name == "read_file":
            result = read_file(tool_input["path"])
        elif tool_name == "read_multiple_files":
            result = read_multiple_files(tool_input["paths"])
        elif tool_name == "list_files":
            result = list_files(tool_input.get("path", "."))
        elif tool_name == "tavily_search":
            result = tavily_search(tool_input["query"])
        elif tool_name == "stop_process":
            result = stop_process(tool_input["process_id"])
        elif tool_name == "execute_code":
            process_id, execution_result = await execute_code(tool_input["code"])
            analysis_task = asyncio.create_task(send_to_ai_for_executing(tool_input["code"], execution_result))
            analysis = await analysis_task
            result = f"{execution_result}\n\nAnalysis:\n{analysis}"
            if process_id in global_state.running_processes:
                result += "\n\nNote: The process is still running in the background."
        else:
            is_error = True
            result = f"Unknown tool: {tool_name}"

        return {"content": result, "is_error": is_error}
    except KeyError as exc:
        logging.error("Missing required parameter %s for tool %s", str(exc), tool_name)
        return {
            "content": f"Error: Missing required parameter {str(exc)} for tool {tool_name}",
            "is_error": True,
        }
    except Exception as exc:
        logging.error("Error executing tool %s: %s", tool_name, str(exc))
        return {
            "content": f"Error executing tool {tool_name}: {str(exc)}",
            "is_error": True,
        }


async def chat_with_llm(user_input: str, image_path=None, current_iteration=None, max_iterations=None):
    """Send the user input to the AI for a response."""

    # This function uses MAINMODEL, which maintains context across calls
    current_conversation = []

    if image_path:
        console.print(
            Panel(
                f"Processing image at path: {image_path}",
                title_align="left",
                title="Image Processing",
                expand=False,
                style="yellow",
            )
        )
        image_base64 = encode_image_to_base64(image_path)

        if image_base64.startswith("Error"):
            console.print(
                Panel(
                    f"Error encoding image: {image_base64}",
                    title="Error",
                    style="bold red",
                )
            )
            return (
                "I'm sorry, there was an error processing the image. Please try again.",
                False,
            )

        image_message = {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_base64,
                    },
                },
                {"type": "text", "text": f"User input for image: {user_input}"},
            ],
        }
        current_conversation.append(image_message)
        console.print(
            Panel(
                "Image message added to conversation history",
                title_align="left",
                title="Image Added",
                style="green",
            )
        )
    else:
        current_conversation.append({"role": "user", "content": user_input})

    # Filter conversation history to maintain context
    filtered_conversation_history = []
    for message in global_state.conversation_history:
        if isinstance(message["content"], list):
            filtered_content = [
                content
                for content in message["content"]
                if content.get("type") != "tool_result"
                or (
                    content.get("type") == "tool_result"
                    and not any(
                        keyword in content.get("output", "")
                        for keyword in [
                            "File contents updated in system prompt",
                            "File created and added to system prompt",
                            "has been read and stored in the system prompt",
                        ]
                    )
                )
            ]
            if filtered_content:
                filtered_conversation_history.append({**message, "content": filtered_content})
        else:
            filtered_conversation_history.append(message)

    # Combine filtered history with current conversation to maintain context
    messages = filtered_conversation_history + current_conversation

    try:
        # MAINMODEL call, which maintains context
        llm_provider: LLMProvider = get_llm_provider(global_state.LLM_PROVIDER)
        response = await llm_provider.create_message(
            model=global_state.MAIN_MODEL,
            system=update_system_prompt(current_iteration, max_iterations),
            messages=messages,
            tools=TOOL_SCHEMA,
            tool_choice={"type": "auto"},
        )
        # Update token usage for MAIN_MODEL
        global_state.main_model_tokens.input += response.usage.input_tokens
        global_state.main_model_tokens.output += response.usage.output_tokens
    except Exception as exc:
        console.print(Panel(f"LLM Provider Error: {str(exc)}", title="API Error", style="bold red"))
        return (
            "I'm sorry, there was an error communicating with the LLM provider. Please try again.",
            False,
        )

    assistant_response = ""
    exit_continuation = False
    tool_uses = []

    for content_block in response.content:
        if content_block.type == "text":
            assistant_response += content_block.text
            if global_state.CONTINUATION_EXIT_PHRASE in content_block.text:
                exit_continuation = True
        elif content_block.type == "tool_use":
            tool_uses.append(content_block)

    console.print(
        Panel(
            Markdown(assistant_response),
            title="CodeMason's Response",
            title_align="left",
            border_style="blue",
            expand=False,
        )
    )

    # Display files in context
    if global_state.file_contents:
        files_in_context = "\n".join(global_state.file_contents.keys())
    else:
        files_in_context = "No files in context. Read, create, or edit files to add."
    console.print(
        Panel(
            files_in_context,
            title="Files in Context",
            title_align="left",
            border_style="white",
            expand=False,
        )
    )

    for tool_use in tool_uses:
        tool_name = tool_use.name
        tool_input = tool_use.input
        tool_use_id = tool_use.id

        console.print(Panel(f"Tool Used: {tool_name}", style="green"))
        console.print(Panel(f"Tool Input: {json.dumps(tool_input, indent=2)}", style="green"))

        tool_result = await execute_tool(tool_name, tool_input)

        if tool_result["is_error"]:
            console.print(
                Panel(
                    tool_result["content"],
                    title="Tool Execution Error",
                    style="bold red",
                )
            )
        else:
            console.print(
                Panel(
                    tool_result["content"],
                    title_align="left",
                    title="Tool Result",
                    style="green",
                )
            )

        current_conversation.append(
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": tool_use_id,
                        "name": tool_name,
                        "input": tool_input,
                    }
                ],
            }
        )

        current_conversation.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": tool_result["content"],
                        "is_error": tool_result["is_error"],
                    }
                ],
            }
        )

        # Update the file_contents dictionary if applicable
        if tool_name in ["create_file", "edit_and_apply", "read_file"] and not tool_result["is_error"]:
            if "path" in tool_input:
                file_path = tool_input["path"]
                if (
                    "File contents updated in system prompt" in tool_result["content"]
                    or "File created and added to system prompt" in tool_result["content"]
                    or "has been read and stored in the system prompt" in tool_result["content"]
                ):
                    # The file_contents dictionary is already updated in the tool function
                    pass

        messages = filtered_conversation_history + current_conversation

        try:
            llm_provider: LLMProvider = get_llm_provider(global_state.LLM_PROVIDER)
            tool_response = await llm_provider.create_message(
                model=global_state.TOOL_CHECKER_MODEL,
                system=update_system_prompt(current_iteration, max_iterations),
                messages=messages,
                tools=TOOL_SCHEMA,
                tool_choice={"type": "auto"},
            )
            # Update token usage for tool checker
            global_state.tool_checker_tokens.input += tool_response.usage.input_tokens
            global_state.tool_checker_tokens.output += tool_response.usage.output_tokens

            tool_checker_response = ""
            for tool_content_block in tool_response.content:
                if tool_content_block.type == "text":
                    tool_checker_response += tool_content_block.text
            console.print(
                Panel(
                    Markdown(tool_checker_response),
                    title="CodeMason's Response to Tool Result",
                    title_align="left",
                    expand=False,
                    box=SIMPLE,
                )
            )
            assistant_response += "\n\n" + tool_checker_response
        except Exception as exc:
            error_message = f"Error in LLM provider response: {str(exc)}"
            console.print(Panel(error_message, title="Error", style="bold red"))
            assistant_response += f"\n\n{error_message}"

    if assistant_response:
        current_conversation.append({"role": "assistant", "content": assistant_response})

    global_state.conversation_history = messages + [{"role": "assistant", "content": assistant_response}]

    # Display token usage at the end
    display_token_usage()

    return assistant_response, exit_continuation
