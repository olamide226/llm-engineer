import asyncio
import signal
import os

from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style

from src.console import Panel, console
from src.global_state import global_state
from src.tools.chat_session import save_chat
from src.tools.tool_agent import chat_with_llm
from src.tools.utils import reset_conversation


async def get_user_input(prompt="You: ") -> str:
    """Get user input from the console."""
    style = Style.from_dict(
        {
            "prompt": "cyan bold",
        }
    )
    session = PromptSession(style=style)
    return await session.prompt_async(prompt, multiline=False)

async def handle_automode(user_input: str):
    """Handle the automode command."""
    try:
        parts = user_input.split()
        if len(parts) > 1 and parts[1].isdigit():
            max_iterations = int(parts[1])
        else:
            max_iterations = global_state.MAX_CONTINUATION_ITERATIONS

        automode = True
        console.print(
            Panel(
                f"Entering automode with {max_iterations} iterations. Please provide the goal of the automode.",
                title_align="left",
                title="Automode",
                style="bold yellow",
            )
        )
        console.print(
            Panel(
                "Press Ctrl+C at any time to exit the automode loop.",
                style="bold yellow",
            )
        )
        user_input = await get_user_input()

        iteration_count = 0
        try:
            while automode and iteration_count < max_iterations:
                response, exit_continuation = await chat_with_llm(
                    user_input,
                    current_iteration=iteration_count + 1,
                    max_iterations=max_iterations,
                )

                if exit_continuation or global_state.CONTINUATION_EXIT_PHRASE in response:
                    console.print(
                        Panel(
                            "Automode completed.",
                            title_align="left",
                            title="Automode",
                            style="green",
                        )
                    )
                    automode = False
                    
                else:
                    console.print(
                        Panel(
                            f"Continuation iteration {iteration_count + 1} completed. Press Ctrl+C to exit automode. ",
                            title_align="left",
                            title="Automode",
                            style="yellow",
                        )
                    )
                    user_input = "Continue with the next step. Or STOP by saying 'AUTOMODE_COMPLETE' if you think you've achieved the results established in the original request."
                iteration_count += 1

                if iteration_count >= max_iterations:
                    console.print(
                        Panel(
                            "Max iterations reached. Exiting automode.",
                            title_align="left",
                            title="Automode",
                            style="bold red",
                        )
                    )
                    automode = False
        except KeyboardInterrupt:
            console.print(
                Panel(
                    "\nAutomode interrupted by user. Exiting automode.",
                    title_align="left",
                    title="Automode",
                    style="bold red",
                )
            )
            automode = False
            if global_state.conversation_history and global_state.conversation_history[-1]["role"] == "user":
                global_state.conversation_history.append(
                    {
                        "role": "assistant",
                        "content": "Automode interrupted. How can I assist you further?",
                    }
                )
    except KeyboardInterrupt:
        console.print(
            Panel(
                "\nAutomode interrupted by user. Exiting automode.",
                title_align="left",
                title="Automode",
                style="bold red",
            )
        )
        automode = False
        if global_state.conversation_history and global_state.conversation_history[-1]["role"] == "user":
            global_state.conversation_history.append(
                {
                    "role": "assistant",
                    "content": "Automode interrupted. How can I assist you further?",
                }
            )

async def main():
    """Main function to run the chat loop."""
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, lambda: print("SIGINT received, shutting down..."))
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
    console.print("While in automode, press Ctrl+C at any time to exit the automode to return to regular chat.")

    while True:
        user_input = await get_user_input()

        if not user_input.strip():
            continue

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
            image_path = (
                (await get_user_input("Drag and drop your image here, then press enter: ")).strip().replace("'", "")
            )

            if os.path.isfile(image_path):
                user_input = await get_user_input("You (prompt for image): ")
                response, _ = await chat_with_llm(user_input, image_path)
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
            await handle_automode(user_input)

            console.print(Panel("Exited automode. Returning to regular chat.", style="green"))
        else:
            response, _ = await chat_with_llm(user_input)


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
