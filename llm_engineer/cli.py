import asyncio
import os

import typer

from llm_engineer.console import Panel, console
from llm_engineer.global_state import global_state
from llm_engineer.main import main, handle_autonomous_mode, chat_with_llm

app = typer.Typer(help="CodeMason AI Engineer Co-Pilot CLI")


@app.command()
def chat(
    model: str = typer.Option(None, "--model", "-m", help="Model to use (default from config)"),
    provider: str = typer.Option(None, "--provider", "-p", help="LLM provider to use (default from config)"),
):
    """Start interactive chat session"""
    try:
        if model:
            global_state.MAIN_MODEL = model
        if provider:
            global_state.LLM_PROVIDER = provider
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print(Panel("Goodbye!", style="bold green"))


@app.command()
def auto(
    iterations: int = typer.Option(
        global_state.MAX_CONTINUATION_ITERATIONS, "--iterations", "-i", help="Number of autonomous mode iterations"
    ),
    goal: str = typer.Argument(..., help="Goal for autonomous mode"),
):
    """Run in autonomous mode with specified iterations and goal"""
    try:
        asyncio.run(handle_autonomous_mode(f"automode {iterations}\n{goal}"))
    except KeyboardInterrupt:
        console.print(Panel("Autonomous mode interrupted", style="bold red"))


@app.command()
def image(
    image_path: str = typer.Argument(..., help="Path to image file"),
    prompt: str = typer.Argument(..., help="Prompt for image analysis"),
):
    """Analyze an image with a prompt"""
    try:
        if not os.path.isfile(image_path):
            console.print(Panel("Invalid image path", style="bold red"))
            raise typer.Exit(1)
        asyncio.run(chat_with_llm(prompt, image_path))
    except KeyboardInterrupt:
        console.print(Panel("Image analysis interrupted", style="bold red"))

@app.command()
def show_help():
    """Show help message"""
    typer.echo(app.info.help)


if __name__ == "__main__":
    app()
