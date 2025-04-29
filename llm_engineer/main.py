"""
Main entry point for the CodeMason Engineer Chat application.

This module provides an interactive chat interface with multi-agent and image processing capabilities.
It handles user input, processes commands, and manages the chat flow, including an autonomous mode
for continuous operation.
"""

import asyncio
import os
import signal

# Third-party imports
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style

# Local imports
from llm_engineer.console import Panel, console
from llm_engineer.global_state import global_state
from llm_engineer.tools.chat_session import save_chat
from llm_engineer.tools.tool_agent import chat_with_llm
from llm_engineer.tools.utils import reset_conversation


async def get_user_input(prompt: str = "You: ") -> str:
    """
    Get user input from the console asynchronously.

    Args:
        prompt (str): The prompt to display to the user. Defaults to "You: ".

    Returns:
        str: The user's input as a string.
    """
    style = Style.from_dict(
        {
            "prompt": "cyan bold",
        }
    )
    session = PromptSession(style=style)
    return await session.prompt_async(prompt, multiline=False)


async def handle_autonomous_mode(user_input: str):
    """
    Handle the autonomous mode command and execution.

    Args:
        user_input (str): The user's input containing the autonomous mode command.
    """
    try:
        parts = user_input.split()
        # Extract the number of iterations from user input, or use default if not provided
        if len(parts) > 1 and parts[1].isdigit():
            max_iterations = int(parts[1])
        else:
            max_iterations = global_state.MAX_CONTINUATION_ITERATIONS

        autonomous_mode = True
        console.print(
            Panel(
                f"Entering autonomous mode with {max_iterations} iterations. Please provide the goal of the autonomous mode.",
                title_align="left",
                title="Autonomous Mode",
                style="bold yellow",
            )
        )
        console.print(
            Panel(
                "Press Ctrl+C at any time to exit the autonomous mode loop.",
                style="bold yellow",
            )
        )
        user_input = await get_user_input()

        iteration_count = 0
        try:
            while autonomous_mode and iteration_count < max_iterations:
                # Process user input and get AI response
                response, exit_continuation = await chat_with_llm(
                    user_input,
                    current_iteration=iteration_count + 1,
                    max_iterations=max_iterations,
                )

                # Check if autonomous mode should be exited
                if exit_continuation or global_state.CONTINUATION_EXIT_PHRASE in response:
                    console.print(
                        Panel(
                            "Autonomous mode completed.",
                            title_align="left",
                            title="Autonomous Mode",
                            style="green",
                        )
                    )
                    autonomous_mode = False
                else:
                    console.print(
                        Panel(
                            f"Continuation iteration {iteration_count + 1} completed. Press Ctrl+C to exit autonomous mode. ",
                            title_align="left",
                            title="Autonomous Mode",
                            style="yellow",
                        )
                    )
                    # Set up the next iteration
                    user_input = "Continue with the next step. Or STOP by saying 'AUTOMODE_COMPLETE' if you think you've achieved the results established in the original request."
                iteration_count += 1

                # Check if max iterations reached
                if iteration_count >= max_iterations:
                    console.print(
                        Panel(
                            "Max iterations reached. Exiting autonomous mode.",
                            title_align="left",
                            title="Autonomous Mode",
                            style="bold red",
                        )
                    )
                    autonomous_mode = False
        except KeyboardInterrupt:
            # Handle user interruption of autonomous mode
            console.print(
                Panel(
                    "\nAutonomous mode interrupted by user. Exiting autonomous mode.",
                    title_align="left",
                    title="Autonomous Mode",
                    style="bold red",
                )
            )
            autonomous_mode = False
            if global_state.conversation_history and global_state.conversation_history[-1]["role"] == "user":
                global_state.conversation_history.append(
                    {
                        "role": "assistant",
                        "content": "Autonomous mode interrupted. How can I assist you further?",
                    }
                )
    except KeyboardInterrupt:
        # Handle user interruption during goal input
        console.print(
            Panel(
                "\nAutonomous mode interrupted by user. Exiting autonomous mode.",
                title_align="left",
                title="Autonomous Mode",
                style="bold red",
            )
        )
        autonomous_mode = False
        if global_state.conversation_history and global_state.conversation_history[-1]["role"] == "user":
            global_state.conversation_history.append(
                {
                    "role": "assistant",
                    "content": "Autonomous mode interrupted. How can I assist you further?",
                }
            )


async def main():
    """
    Main function to run the chat loop.

    This function sets up signal handling, displays welcome messages,
    and manages the main chat loop, including handling various user commands.
    """
    loop = asyncio.get_running_loop()
    # Set up signal handler for graceful shutdown
    loop.add_signal_handler(signal.SIGINT, lambda: print("SIGINT received, shutting down..."))

    # Display welcome messages and instructions
    console.print(
        Panel(
            "Welcome to the CodeMason Engineer Chat with Multi-Agent and Image Abilities!",
            title="Welcome",
            style="bold green",
        )
    )
    console.print("Type 'exit' to end the conversation.")
    console.print("Type 'image' to include an image in your message.")
    console.print("Type 'automode [number]' to enter Autonomous mode with a specific number of iterations.")
    console.print("Type 'reset' to clear the conversation history.")
    console.print("Type 'save chat' to save the conversation to a Markdown file.")
    console.print(
        "While in autonomous mode, press Ctrl+C at any time to exit the autonomous mode to return to regular chat."
    )

    while True:
        user_input = await get_user_input()

        if not user_input.strip():
            continue

        # Handle various user commands
        if user_input.lower() == "exit":
            console.print(
                Panel(
                    "Thank you for chatting. Goodbye!",
                    title_align="left",
                    title="Goodbye",
                    style="bold green",
                )
            )
            break

        if user_input.lower() == "reset":
            reset_conversation()
            continue

        if user_input.lower() == "save chat":
            filename = save_chat()
            console.print(Panel(f"Chat saved to {filename}", title="Chat Saved", style="bold green"))
            continue

        if user_input.lower() == "image":
            # Handle image input
            image_path = (
                (await get_user_input("Drag and drop your image here, then press enter: ")).strip().replace("'", "")
            )

            if os.path.isfile(image_path):
                user_input = await get_user_input("You (prompt for image): ")
                _response, _ = await chat_with_llm(user_input, image_path)
            else:
                console.print(
                    Panel(
                        "Invalid image path. Please try again.",
                        title="Error",
                        style="bold red",
                    )
                )
                continue
        elif user_input.lower().startswith("automode"):
            # Handle autonomous mode
            await handle_autonomous_mode(user_input)

            console.print(Panel("Exited autonomous mode. Returning to regular chat.", style="green"))
        else:
            # Process regular user input
            _response, _ = await chat_with_llm(user_input)

def start():
    """Start the chat loop."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print(
            Panel(
                "Thank you for chatting. Goodbye!",
                title_align="left",
                title="Goodbye",
                style="bold green",
            )
        )


if __name__ == "__main__":
    start()
