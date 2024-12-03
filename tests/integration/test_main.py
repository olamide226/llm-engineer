import pytest
from unittest.mock import patch, Mock
from llm_engineer.main import start, chat_with_llm
from llm_engineer.global_state import global_state
from unittest.mock import patch, AsyncMock, Mock
from llm_engineer.main import main, get_user_input, handle_autonomous_mode

@pytest.fixture
def mock_llm_provider():
    with patch('llm_engineer.tools.tool_agent.get_llm_provider') as mock_get_provider:
        mock_provider = Mock()
        mock_provider.create_message.return_value = Mock(
            content=[Mock(text="Test response")],
            usage=Mock(input_tokens=10, output_tokens=20)
        )
        mock_get_provider.return_value = mock_provider
        yield mock_provider

@pytest.mark.asyncio
async def test_chat_with_llm(mock_llm_provider):
    user_input = "Test message"
    response, exit_continuation = await chat_with_llm(user_input)

    mock_llm_provider.create_message.assert_called_once()
    assert "Test response" in response
    assert not exit_continuation

@pytest.mark.asyncio
async def test_chat_with_llm_continuation(mock_llm_provider):
    user_input = "Test message"
    mock_llm_provider.create_message.return_value = Mock(
        content=[Mock(text=f"Test response {global_state.CONTINUATION_EXIT_PHRASE}")],
        usage=Mock(input_tokens=10, output_tokens=20)
    )

    response, exit_continuation = await chat_with_llm(user_input)

    assert global_state.CONTINUATION_EXIT_PHRASE in response
    assert exit_continuation

@patch('llm_engineer.main.asyncio.run')
def test_start(mock_run):
    start()
    mock_run.assert_called_once()
    @pytest.mark.asyncio
    async def test_get_user_input():
        with patch('llm_engineer.main.PromptSession.prompt_async', new_callable=AsyncMock) as mock_prompt:
            mock_prompt.return_value = "Test input"
            result = await get_user_input()
            assert result == "Test input"
            mock_prompt.assert_called_once_with("You: ", multiline=False)

    @pytest.mark.asyncio
    async def test_handle_autonomous_mode():
        user_input = "automode 3"
        with patch('llm_engineer.main.get_user_input', new_callable=AsyncMock) as mock_get_user_input, \
             patch('llm_engineer.main.chat_with_llm', new_callable=AsyncMock) as mock_chat_with_llm, \
             patch('llm_engineer.main.console.print') as mock_console_print:
            
            mock_get_user_input.side_effect = ["Goal", "Continue", "Continue", "AUTOMODE_COMPLETE"]
            mock_chat_with_llm.side_effect = [
                ("Response 1", False),
                ("Response 2", False),
                ("Response 3", True)
            ]
            
            await handle_autonomous_mode(user_input)
            
            assert mock_get_user_input.call_count == 4
            assert mock_chat_with_llm.call_count == 3
            mock_console_print.assert_any_call(Mock())

    @pytest.mark.asyncio
    async def test_main():
        with patch('llm_engineer.main.get_user_input', new_callable=AsyncMock) as mock_get_user_input, \
             patch('llm_engineer.main.console.print') as mock_console_print, \
             patch('llm_engineer.main.reset_conversation') as mock_reset_conversation, \
             patch('llm_engineer.main.save_chat') as mock_save_chat, \
             patch('llm_engineer.main.chat_with_llm', new_callable=AsyncMock) as mock_chat_with_llm, \
             patch('llm_engineer.main.handle_autonomous_mode', new_callable=AsyncMock) as mock_handle_autonomous_mode:
            
            mock_get_user_input.side_effect = [
                "exit", "reset", "save chat", "image", "automode 3", "regular input"
            ]
            mock_save_chat.return_value = "chat.md"
            mock_chat_with_llm.return_value = ("Response", False)
            
            await main()
            
            assert mock_get_user_input.call_count == 6
            assert mock_console_print.call_count >= 6
            mock_reset_conversation.assert_called_once()
            mock_save_chat.assert_called_once()
            mock_chat_with_llm.assert_called_once_with("regular input")
            mock_handle_autonomous_mode.assert_called_once_with("automode 3")
# Add more integration tests as needed, such as testing file operations, web searches, etc.