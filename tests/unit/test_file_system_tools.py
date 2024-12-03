import asyncio
import json
from unittest.mock import MagicMock, mock_open, patch

import pytest

from llm_engineer.global_state import global_state
from llm_engineer.tools.file_system import (
    apply_edits,
    create_file,
    create_folder,
    edit_and_apply,
    execute_code,
    list_files,
    read_file,
    read_multiple_files,
    setup_virtual_environment,
    stop_process,
)


@pytest.fixture
def mock_global_state():
    global_state.file_contents = {}
    global_state.running_processes = {}
    yield
    global_state.file_contents = {}
    global_state.running_processes = {}

@patch("llm_engineer.tools.file_system.venv.create")
@patch("llm_engineer.tools.file_system.os.path.exists", return_value=False)
@patch("llm_engineer.tools.file_system.os.getcwd", return_value="/test")
def test_setup_virtual_environment(mock_getcwd, mock_exists, mock_create):
    venv_path, activate_script = setup_virtual_environment()
    assert venv_path == "/test/code_execution_env"
    assert activate_script == "/test/code_execution_env/bin/activate"

@patch("llm_engineer.tools.file_system.os.makedirs")
def test_create_folder(mock_makedirs):
    result = create_folder("/test/folder")
    assert result == "Folder created: /test/folder"

@patch("llm_engineer.tools.file_system.os.makedirs", side_effect=Exception("Error"))
def test_create_folder_error(mock_makedirs):
    result = create_folder("/test/folder")
    assert result == "Error creating folder: Error"

@patch("builtins.open", new_callable=mock_open)
def test_create_file(mock_open, mock_global_state):
    result = create_file("/test/file.txt", "content")
    assert result == "File created and added to system prompt: /test/file.txt"
    mock_open.assert_called_with("/test/file.txt", "w")
    assert global_state.file_contents["/test/file.txt"] == "content"

@patch("builtins.open", new_callable=mock_open)
def test_create_file_error(mock_open):
    mock_open.side_effect = Exception("Error")
    result = create_file("/test/file.txt", "content")
    assert result == "Error creating file: Error"

@patch("llm_engineer.tools.file_system.setup_virtual_environment", return_value=("/test/env", "/test/env/bin/activate"))
@patch("llm_engineer.tools.file_system.asyncio.create_subprocess_shell")
@patch("llm_engineer.tools.file_system.asyncio.wait_for", side_effect=asyncio.TimeoutError)
def test_execute_code_timeout(mock_wait_for, mock_create_subprocess_shell, mock_setup_virtual_environment):
    async def run_test():
        process_id, execution_result = await execute_code("print('Hello')")
        assert execution_result == "Process ID: process_0\n\nStdout:\nProcess started and running in the background.\n\nStderr:\n\n\nReturn Code: Running"

    asyncio.run(run_test())

@patch("builtins.open", new_callable=mock_open, read_data="file content")
def test_read_file(mock_open, mock_global_state):
    result = read_file("/test/file.txt")
    assert result == "File '/test/file.txt' has been read and stored in the system prompt."
    mock_open.assert_called_with("/test/file.txt", "r")
    assert global_state.file_contents["/test/file.txt"] == "file content"

@patch("builtins.open", new_callable=mock_open)
def test_read_file_error(mock_open):
    mock_open.side_effect = Exception("Error")
    result = read_file("/test/file.txt")
    assert result == "Error reading file: Error"

@patch("builtins.open", new_callable=mock_open, read_data="file content")
def test_read_multiple_files(mock_open, mock_global_state):
    result = read_multiple_files(["/test/file1.txt", "/test/file2.txt"])
    assert "File '/test/file1.txt' has been read and stored in the system prompt." in result
    assert "File '/test/file2.txt' has been read and stored in the system prompt." in result
    assert global_state.file_contents["/test/file1.txt"] == "file content"
    assert global_state.file_contents["/test/file2.txt"] == "file content"

@patch("builtins.open", new_callable=mock_open)
def test_read_multiple_files_error(mock_open):
    mock_open.side_effect = Exception("Error")
    result = read_multiple_files(["/test/file1.txt", "/test/file2.txt"])
    assert "Error reading file '/test/file1.txt': Error" in result
    assert "Error reading file '/test/file2.txt': Error" in result

@patch("llm_engineer.tools.file_system.os.listdir", return_value=["file1.txt", "file2.txt"])
def test_list_files(mock_listdir):
    result = list_files("/test")
    assert result == "file1.txt\nfile2.txt"

@patch("llm_engineer.tools.file_system.os.listdir", side_effect=Exception("Error"))
def test_list_files_error(mock_listdir):
    result = list_files("/test")
    assert result == "Error listing files: Error"

@patch("llm_engineer.tools.file_system.os.killpg")
@patch("llm_engineer.tools.file_system.os.getpgid", return_value=1234)
def test_stop_process(mock_getpgid, mock_killpg, mock_global_state):
    global_state.running_processes["process_0"] = MagicMock(pid=1234)
    result = stop_process("process_0")
    assert result == "Process process_0 has been stopped."

def test_stop_process_not_found(mock_global_state):
    result = stop_process("process_0")
    assert result == "No running process found with ID process_0."

@patch("llm_engineer.tools.file_system.generate_edit_instructions", return_value=json.dumps([{"search": "old", "replace": "new"}]))
@patch("llm_engineer.tools.file_system.apply_edits", return_value=("new content", True, ""))
@patch("builtins.open", new_callable=mock_open, read_data="old content")
def test_edit_and_apply(mock_open, mock_apply_edits, mock_generate_edit_instructions, mock_global_state):
    async def run_test():
        result = await edit_and_apply("/test/file.txt", "instructions", "context")
        assert result == "Changes applied to /test/file.txt"

    asyncio.run(run_test())

@patch("llm_engineer.tools.file_system.generate_edit_instructions", return_value=json.dumps([{"search": "old", "replace": "new"}]))
@patch("llm_engineer.tools.file_system.apply_edits", return_value=("new content", False, ""))
@patch("builtins.open", new_callable=mock_open, read_data="old content")
def test_edit_and_apply_no_changes(mock_open, mock_apply_edits, mock_generate_edit_instructions, mock_global_state):
    async def run_test():
        result = await edit_and_apply("/test/file.txt", "instructions", "context")
        assert result == "No changes could be applied to /test/file.txt after 3 attempts. Please review the edit instructions and try again."

    asyncio.run(run_test())

@patch("llm_engineer.tools.file_system.generate_diff", return_value="diff")
@patch("builtins.open", new_callable=mock_open, read_data="old content")
def test_apply_edits(mock_generate_diff, mock_open):
    original_content = "old content"
    edit_instructions = [{"search": "old", "replace": "new"}]
    async def run_test():
        new_content, success, error_message = await apply_edits("/test/file.txt", edit_instructions, original_content)
        assert new_content == "new content"
        assert success
        assert error_message == ""

    asyncio.run(run_test())

@patch("llm_engineer.tools.file_system.generate_diff", side_effect=Exception("Error"))
@patch("builtins.open", new_callable=mock_open, read_data="old content")
def test_apply_edits_error(mock_generate_diff, mock_open):
    original_content = "old content"
    edit_instructions = [{"search": "old", "replace": "new"}]
    async def run_test():
        new_content, success, error_message = await apply_edits("/test/file.txt", edit_instructions, original_content)
        assert new_content == original_content
        assert not success
        assert error_message == "Error"

    asyncio.run(run_test())