import asyncio
import json
import logging
import os
import re
import signal
import sys
import venv
from typing import Tuple

from src.console import BarColumn, Panel, Progress, SpinnerColumn, TextColumn, console
from src.global_state import global_state
from src.tools.utils import generate_diff, generate_edit_instructions


def setup_virtual_environment() -> Tuple[str, str]:
    """Set up a virtual environment and return the path and activation script"""
    venv_name = "code_execution_env"
    venv_path = os.path.join(os.getcwd(), venv_name)
    try:
        if not os.path.exists(venv_path):
            venv.create(venv_path, with_pip=True)

        # Activate the virtual environment
        if sys.platform == "win32":
            activate_script = os.path.join(venv_path, "Scripts", "activate.bat")
        else:
            activate_script = os.path.join(venv_path, "bin", "activate")

        return venv_path, activate_script
    except Exception as e:
        logging.error("Error setting up virtual environment: %s", str(e))
        raise


def create_folder(path: str):
    """Create a new directory at the specified path"""
    try:
        os.makedirs(path, exist_ok=True)
        return f"Folder created: {path}"
    except Exception as e:
        return f"Error creating folder: {str(e)}"


def create_file(path: str, content=""):
    """Create a new file at the specified path with optional content"""
    try:
        with open(path, "w") as f:
            f.write(content)
        global_state.file_contents[path] = content
        return f"File created and added to system prompt: {path}"
    except Exception as e:
        return f"Error creating file: {str(e)}"


async def execute_code(code, timeout=10):
    venv_path, activate_script = setup_virtual_environment()

    # Generate a unique identifier for this process
    process_id = f"process_{len(global_state.running_processes)}"

    # Write the code to a temporary file
    with open(f"{process_id}.py", "w", encoding="utf-8") as f:
        f.write(code)

    # Prepare the command to run the code
    if sys.platform == "win32":
        command = f'"{activate_script}" && python3 {process_id}.py'
    else:
        command = f'source "{activate_script}" && python3 {process_id}.py'

    # Create a process to run the command
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        shell=True,
        preexec_fn=None if sys.platform == "win32" else os.setsid,
    )

    # Store the process in our global dictionary
    global_state.running_processes[process_id] = process

    try:
        # Wait for initial output or timeout
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        stdout = stdout.decode()
        stderr = stderr.decode()
        return_code = process.returncode
    except asyncio.TimeoutError:
        # If we timeout, it means the process is still running
        stdout = "Process started and running in the background."
        stderr = ""
        return_code = "Running"

    execution_result = (
        f"Process ID: {process_id}\n\nStdout:\n{stdout}\n\nStderr:\n{stderr}\n\nReturn Code: {return_code}"
    )
    return process_id, execution_result


def read_file(path):
    try:
        with open(path, "r") as f:
            content = f.read()
        global_state.file_contents[path] = content
        return f"File '{path}' has been read and stored in the system prompt."
    except Exception as e:
        return f"Error reading file: {str(e)}"


def read_multiple_files(paths: list[str]):
    results = []
    for path in paths:
        try:
            with open(path, "r") as f:
                content = f.read()
            global_state.file_contents[path] = content
            results.append(f"File '{path}' has been read and stored in the system prompt.")
        except Exception as ex:
            results.append(f"Error reading file '{path}': {str(ex)}")
    return "\n".join(results)


def list_files(path="."):
    try:
        files = os.listdir(path)
        return "\n".join(files)
    except Exception as ex:
        return f"Error listing files: {str(ex)}"


def stop_process(process_id: int):
    if process_id in global_state.running_processes:
        process = global_state.running_processes[process_id]
        if sys.platform == "win32":
            process.terminate()
        else:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        del global_state.running_processes[process_id]
        return f"Process {process_id} has been stopped."
    else:
        return f"No running process found with ID {process_id}."


async def edit_and_apply(path, instructions, project_context, max_retries=3):
    try:
        original_content = global_state.file_contents.get(path, "")
        if not original_content:
            with open(path, "r") as file:
                original_content = file.read()
            global_state.file_contents[path] = original_content

        for attempt in range(max_retries):
            edit_instructions_json = await generate_edit_instructions(
                path,
                original_content,
                instructions,
                project_context,
                global_state.file_contents,
            )

            if edit_instructions_json:
                # Parse JSON here
                edit_instructions = json.loads(edit_instructions_json)
                console.print(
                    Panel(
                        f"Attempt {attempt + 1}/{max_retries}: The following SEARCH/REPLACE blocks have been generated:",
                        title="Edit Instructions",
                        style="cyan",
                    )
                )
                for i, block in enumerate(edit_instructions, 1):
                    console.print(f"Block {i}:")
                    console.print(
                        Panel(
                            f"SEARCH:\n{block['search']}\n\nREPLACE:\n{block['replace']}",
                            expand=False,
                        )
                    )

                edited_content, changes_made, failed_edits = await apply_edits(
                    path, edit_instructions, original_content
                )

                if changes_made:
                    global_state.file_contents[path] = edited_content  # Update the file_contents with the new content
                    console.print(
                        Panel(
                            f"File contents updated in system prompt: {path}",
                            style="green",
                        )
                    )

                    if failed_edits:
                        console.print(
                            Panel(
                                f"Some edits could not be applied. Retrying...",
                                style="yellow",
                            )
                        )
                        instructions += (
                            f"\n\nPlease retry the following edits that could not be applied:\n{failed_edits}"
                        )
                        original_content = edited_content
                        continue

                    return f"Changes applied to {path}"
                elif attempt == max_retries - 1:
                    return f"No changes could be applied to {path} after {max_retries} attempts. Please review the edit instructions and try again."
                else:
                    console.print(
                        Panel(
                            f"No changes could be applied in attempt {attempt + 1}. Retrying...",
                            style="yellow",
                        )
                    )
            else:
                return f"No changes suggested for {path}"

        return f"Failed to apply changes to {path} after {max_retries} attempts."
    except Exception as e:
        return f"Error editing/applying to file: {str(e)}"


async def apply_edits(file_path, edit_instructions, original_content):
    changes_made = False
    edited_content = original_content
    total_edits = len(edit_instructions)
    failed_edits = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        edit_task = progress.add_task("[cyan]Applying edits...", total=total_edits)

        for i, edit in enumerate(edit_instructions, 1):
            search_content = edit["search"].strip()
            replace_content = edit["replace"].strip()

            # Use regex to find the content, ignoring leading/trailing whitespace
            pattern = re.compile(re.escape(search_content), re.DOTALL)
            match = pattern.search(edited_content)

            if match:
                # Replace the content, preserving the original whitespace
                start, end = match.span()
                # Strip <SEARCH> and <REPLACE> tags from replace_content
                replace_content_cleaned = re.sub(r"</?SEARCH>|</?REPLACE>", "", replace_content)
                edited_content = edited_content[:start] + replace_content_cleaned + edited_content[end:]
                changes_made = True

                # Display the diff for this edit
                diff_result = generate_diff(search_content, replace_content, file_path)
                console.print(
                    Panel(
                        diff_result,
                        title=f"Changes in {file_path} ({i}/{total_edits})",
                        style="cyan",
                    )
                )
            else:
                console.print(
                    Panel(
                        f"Edit {i}/{total_edits} not applied: content not found",
                        style="yellow",
                    )
                )
                failed_edits.append(f"Edit {i}: {search_content}")

            progress.update(edit_task, advance=1)

    if not changes_made:
        console.print(
            Panel(
                "No changes were applied. The file content already matches the desired state.",
                style="green",
            )
        )
    else:
        # Write the changes to the file
        with open(file_path, "w") as file:
            file.write(edited_content)
        console.print(Panel(f"Changes have been written to {file_path}", style="green"))

    return edited_content, changes_made, "\n".join(failed_edits)
