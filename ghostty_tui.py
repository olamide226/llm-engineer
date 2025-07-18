import asyncio # Added for asyncio.sleep
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Header, Footer, Input, Log, TextArea, Static
# Added TextArea, re-added Static as it's still used for #code_editor_area if not changed to TextArea

class GhosttyTUI(App):
    """A basic Textual TUI with an interactive chat area, a code editor pane, and placeholder LLM responses."""

    CSS = """
    /* Ghostty-like Color Palette (Fallback) */
    $ghostty-bg: #282a36;
    $ghostty-fg: #f8f8f2;
    $ghostty-comment: #6272a4;
    $ghostty-cyan: #8be9fd;
    $ghostty-green: #50fa7b;
    $ghostty-orange: #ffb86c;
    $ghostty-pink: #ff79c6;
    $ghostty-purple: #bd93f9;
    $ghostty-red: #ff5555;
    $ghostty-yellow: #f1fa8c;
    $primary-accent: $ghostty-pink;
    $secondary-accent: $ghostty-purple;
    $tertiary-bg: #21222c; /* A slightly darker bg for chat/code areas */

    Screen {
        layout: vertical;
        align: center top;
        background: $ghostty-bg;
        color: $ghostty-fg;
    }

    #chat_area {
        width: 100%;
        height: 70%; /* Allocate 70% of height to chat area */
        border: round $primary-accent;
        background: $tertiary-bg;
        color: $ghostty-fg;
        margin: 1;
        padding: 1;
        overflow-y: auto; /* Allow vertical scrolling if content exceeds height */
    }

    #code_editor_area {
        width: 100%;
        height: 20%; /* Allocate 20% of height to code editor */
        border: round $primary-accent;
        background: $tertiary-bg;
        /* color: $ghostty-fg; TextArea has its own theme for text */
        margin: 1;
        /* padding: 1; Padding can interfere with TextArea's own layout */
        overflow-y: auto; /* Should be handled by TextArea itself */
    }

    /* TextArea specific styling - very basic for now */
    TextArea {
        background: $tertiary-bg;
        color: $ghostty-fg; /* Default text color */
    }
    /* Example: if you wanted to style the selection (might need !important or more specific selector) */
    /*
    TextArea > .text-area--selection {
        background: $ghostty-purple;
        color: $ghostty-bg;
    }
    */

    #user_input_area_container {
        width: 100%;
        height: 10%; /* Allocate 10% of height to input area */
        align: center bottom; /* Align input to the bottom of this container */
        padding: 1 0 0 0; /* Adjusted padding */
    }

    #user_input_area {
        width: 100%;
        border: round $secondary-accent;
        background: $tertiary-bg; /* Consistent with other areas */
        color: $ghostty-fg;
        padding: 0 1; /* Padding inside the input field */
        height: 100%; /* Make input take full height of its container */
    }
    """

    TITLE = "Ghostty TUI (Themed)"

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the application's layout."""
        yield Header()
        yield Log(id="chat_area")
        yield TextArea(text="// Type your code here...\n", id="code_editor_area", language="python", theme="vscode_dark")
        # Using a built-in dark theme for TextArea for better out-of-the-box syntax highlighting appearance
        # The explicit background and color in CSS for TextArea will ensure base colors match.
        with Vertical(id="user_input_area_container"):
            yield Input(placeholder="Type your message here...", id="user_input_area")
        yield Footer()

    async def get_llm_response(self, user_message: str) -> str:
        """Placeholder for actual LLM call."""
        await asyncio.sleep(0.5) # Simulate network latency
        return f"LLM (placeholder): You said '{user_message}'"

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle the Input.Submitted event."""
        if event.input.id == "user_input_area":
            message = event.value
            if message:
                chat_log = self.query_one("#chat_area", Log)
                chat_log.write_line(f"You: {message}")
                event.input.value = "" # Clear the input

                llm_response = await self.get_llm_response(message)
                chat_log.write_line(f"Bot: {llm_response}")

if __name__ == "__main__":
    app = GhosttyTUI()
    app.run()
