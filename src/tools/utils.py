import base64
import difflib
import io
import json
import re
from typing import Optional

from PIL import Image
import httpx

from src.console import ROUNDED, Panel, Syntax, Table, console
from src.global_state import TokenTracking, global_state
from src.prompts.automode import AUTOMODE_SYSTEM_PROMPT
from src.prompts.base_system_prompt import BASE_SYSTEM_PROMPT
from src.providers import get_llm_provider
from src.config import config
from dotenv import load_dotenv, set_key


def update_system_prompt(
    current_iteration: Optional[int] = None,
    max_iterations: Optional[int] = None,
    automode=False,
) -> str:
    chain_of_thought_prompt = """
    Answer the user's request using relevant tools (if they are available). Before calling a tool, do some analysis within <thinking></thinking> tags. First, think about which of the provided tools is the relevant tool to answer the user's request. Second, go through each of the required parameters of the relevant tool and determine if the user has directly provided or given enough information to infer a value. When deciding if the parameter can be inferred, carefully consider all the context to see if it supports a specific value. If all of the required parameters are present or can be reasonably inferred, close the thinking tag and proceed with the tool call. BUT, if one of the values for a required parameter is missing, DO NOT invoke the function (not even with fillers for the missing params) and instead, ask the user to provide the missing parameters. DO NOT ask for more information on optional parameters if it is not provided.

    Do not reflect on the quality of the returned search results in your response.
    """

    file_contents_prompt = "\n\nFile Contents:\n"
    for path, content in global_state.file_contents.items():
        file_contents_prompt += f"\n--- {path} ---\n{content}\n"

    if automode:
        iteration_info = ""
        if current_iteration is not None and max_iterations is not None:
            iteration_info = f"You are currently on iteration {current_iteration} out of {max_iterations} in automode."
        return (
            BASE_SYSTEM_PROMPT
            + file_contents_prompt
            + "\n\n"
            + AUTOMODE_SYSTEM_PROMPT.format(iteration_info=iteration_info)
            + "\n\n"
            + chain_of_thought_prompt
        )
    else:
        return BASE_SYSTEM_PROMPT + file_contents_prompt + "\n\n" + chain_of_thought_prompt


def encode_image_to_base64(image_path):
    try:
        with Image.open(image_path) as img:
            max_size = (1024, 1024)
            img.thumbnail(max_size, Image.DEFAULT_STRATEGY)
            if img.mode != "RGB":
                img = img.convert("RGB")
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format="JPEG")
            return base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")
    except Exception as e:
        return f"Error encoding image: {str(e)}"


def reset_code_editor_memory():
    global_state.code_editor_memory = []
    console.print(Panel("Code editor memory has been reset.", title="Reset", style="bold green"))


def reset_conversation():
    """Reset the conversation history, token counts, file contents, code editor memory, and code editor files."""
    global_state.conversation_history = []
    global_state.main_model_tokens = TokenTracking()
    global_state.tool_checker_tokens = TokenTracking()
    global_state.code_editor_tokens = TokenTracking()
    global_state.code_execution_tokens = TokenTracking()
    global_state.file_contents = {}
    global_state.code_editor_files = set()
    reset_code_editor_memory()
    console.print(
        Panel(
            "Conversation history, token counts, file contents, code editor memory, and code editor files have been reset.",
            title="Reset",
            style="bold green",
        )
    )
    display_token_usage()


def display_token_usage():

    table = Table(box=ROUNDED)
    table.add_column("Model", style="cyan")
    table.add_column("Input", style="magenta")
    table.add_column("Output", style="magenta")
    table.add_column("Total", style="green")
    table.add_column(f"% of Context ({global_state.MAX_CONTEXT_TOKENS:,})", style="yellow")
    table.add_column("Cost ($)", style="red")

    model_costs = {
        "Main Model": {"input": 3.00, "output": 15.00, "has_context": True},
        "Tool Checker": {"input": 3.00, "output": 15.00, "has_context": False},
        "Code Editor": {"input": 3.00, "output": 15.00, "has_context": True},
        "Code Execution": {"input": 3.00, "output": 15.00, "has_context": False},
    }

    total_input = 0
    total_output = 0
    total_cost = 0
    total_context_tokens = 0

    for model, tokens in [
        ("Main Model", global_state.main_model_tokens.model_dump()),
        ("Tool Checker", global_state.tool_checker_tokens.model_dump()),
        ("Code Editor", global_state.code_editor_tokens.model_dump()),
        ("Code Execution", global_state.code_execution_tokens.model_dump()),
    ]:
        input_tokens = tokens["input"]
        output_tokens = tokens["output"]
        total_tokens = input_tokens + output_tokens

        total_input += input_tokens
        total_output += output_tokens

        input_cost = (input_tokens / 1_000_000) * model_costs[model]["input"]
        output_cost = (output_tokens / 1_000_000) * model_costs[model]["output"]
        model_cost = input_cost + output_cost
        total_cost += model_cost

        if model_costs[model]["has_context"]:
            total_context_tokens += total_tokens
            percentage = (total_tokens / global_state.MAX_CONTEXT_TOKENS) * 100
        else:
            percentage = 0

        table.add_row(
            model,
            f"{input_tokens:,}",
            f"{output_tokens:,}",
            f"{total_tokens:,}",
            (f"{percentage:.2f}%" if model_costs[model]["has_context"] else "Doesn't save context"),
            f"${model_cost:.3f}",
        )

    grand_total = total_input + total_output
    # total_percentage = (total_context_tokens / global_state.MAX_CONTEXT_TOKENS) * 100

    table.add_row(
        "Total",
        f"{total_input:,}",
        f"{total_output:,}",
        f"{grand_total:,}",
        "",  # Empty string for the "% of Context" column
        f"${total_cost:.3f}",
        style="bold",
    )

    console.print(table)


def highlight_diff(diff_text):
    return Syntax(diff_text, "diff", theme="monokai", line_numbers=True)


async def generate_edit_instructions(
    file_path: str,
    file_content: str,
    instructions: str,
    project_context: str,
    full_file_contents,
):
    try:
        # Prepare memory context (this is the only part that maintains some context between calls)
        memory_context = "\n".join([f"Memory {i+1}:\n{mem}" for i, mem in enumerate(global_state.code_editor_memory)])

        # Prepare full file contents context, excluding the file being edited if it's already in code_editor_files
        full_file_contents_context = "\n\n".join(
            [
                f"--- {path} ---\n{content}"
                for path, content in full_file_contents.items()
                if path != file_path or path not in global_state.code_editor_files
            ]
        )

        system_prompt = f"""
        You are an AI coding agent that generates edit instructions for code files. Your task is to analyze the provided code and generate SEARCH/REPLACE blocks for necessary changes. Follow these steps:

        1. Review the entire file content to understand the context:
        {file_content}

        2. Carefully analyze the specific instructions:
        {instructions}

        3. Take into account the overall project context:
        {project_context}

        4. Consider the memory of previous edits:
        {memory_context}

        5. Consider the full context of all files in the project:
        {full_file_contents_context}

        6. Generate SEARCH/REPLACE blocks for each necessary change. Each block should:
           - Include enough context to uniquely identify the code to be changed
           - Provide the exact replacement code, maintaining correct indentation and formatting
           - Focus on specific, targeted changes rather than large, sweeping modifications

        7. Ensure that your SEARCH/REPLACE blocks:
           - Address all relevant aspects of the instructions
           - Maintain or enhance code readability and efficiency
           - Consider the overall structure and purpose of the code
           - Follow best practices and coding standards for the language
           - Maintain consistency with the project context and previous edits
           - Take into account the full context of all files in the project

        IMPORTANT: RETURN ONLY THE SEARCH/REPLACE BLOCKS. NO EXPLANATIONS OR COMMENTS.
        USE THE FOLLOWING FORMAT FOR EACH BLOCK:

        <SEARCH>
        Code to be replaced
        </SEARCH>
        <REPLACE>
        New code to insert
        </REPLACE>

        If no changes are needed, return an empty list.
        """

        # Make the API call to CODEEDITORMODEL (context is not maintained except for code_editor_memory)
        llm_provider = get_llm_provider(global_state.LLM_PROVIDER)
        response = await llm_provider.create_message(
            model=global_state.MAIN_MODEL,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": "Generate SEARCH/REPLACE blocks for the necessary changes.",
                }
            ],
        )
        # Update token usage for code editor
        global_state.code_editor_tokens.input += response.usage.prompt_tokens
        global_state.code_editor_tokens.output += response.usage.completion_tokens

        # Parse the response to extract SEARCH/REPLACE blocks
        edit_instructions = parse_search_replace_blocks(response.choices[0].message.content)

        # Update code editor memory (this is the only part that maintains some context between calls)
        global_state.code_editor_memory.append(f"Edit Instructions for {file_path}:\n{response.choices[0].message.content}")

        # Add the file to code_editor_files set
        global_state.code_editor_files.add(file_path)

        return edit_instructions

    except Exception as e:
        console.print(f"Error in generating edit instructions: {str(e)}", style="bold red")
        return []  # Return empty list if any exception occurs


def parse_search_replace_blocks(response_text):
    blocks = []
    pattern = r"<SEARCH>\n(.*?)\n</SEARCH>\n<REPLACE>\n(.*?)\n</REPLACE>"
    matches = re.findall(pattern, response_text, re.DOTALL)

    for search, replace in matches:
        blocks.append({"search": search.strip(), "replace": replace.strip()})

    return json.dumps(blocks)  # Keep returning JSON string


def generate_diff(original, new, path):
    diff = list(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
            n=3,
        )
    )

    diff_text = "".join(diff)
    highlighted_diff = highlight_diff(diff_text)

    return highlighted_diff

async def refresh_token() -> None:
    CUSTOM_REFRESH_TOKEN_URL = "/api/v1/auth/refreshtoken"
    url = config.custom_api_host + CUSTOM_REFRESH_TOKEN_URL
    headers = {
        "Authorization": "Bearer " + config.custom_api_token,
        "app-key": config.custom_app_key,
    }
    cookies = {
        'rt': config.custom_refresh_token,
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, cookies=cookies)
        print(response.request.headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Extract Set-Cookie header
        auth_tokens: str = response.headers.get('Set-Cookie')

        # Parse Set-Cookie header to find rt token
        ref_token = next(
            (item.split('=')[1] for item in auth_tokens.split(';') if item.strip().startswith('rt=')),
            None
        )
        # Extract accessToken from JSON response
        response_data = response.json()
        auth_token = response_data.get('accessToken')

        # Update configuration
        config.custom_refresh_token = ref_token
        config.custom_api_token = auth_token

        # Write the updated values back to the .env file
        env_file = ".env"
        load_dotenv(env_file)
        set_key(env_file, 'CUSTOM_API_TOKEN', auth_token)
        set_key(env_file, 'CUSTOM_REFRESH_TOKEN', ref_token)
