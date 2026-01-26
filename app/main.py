import sys
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Input, RichLog
from textual import events
from textual.timer import Timer

from app.commands import run_command


def resource_path(relative_path: str) -> Path:
    """
    Get absolute path to resource (works for normal runs + PyInstaller EXE).
    """
    if hasattr(sys, "_MEIPASS"):
        # PyInstaller temp folder
        base_path = Path(sys._MEIPASS)
    else:
        # Normal project folder
        base_path = Path(__file__).parent

    return base_path / relative_path


class PanthaTerminal(App):
    TITLE = "Pantha Terminal"
    SUB_TITLE = "Neon Purple Terminal UI"

    def __init__(self):
        super().__init__()

        # Force CSS path to work in both dev + EXE
        self.css_file = resource_path("styles.tcss")

        self.glow_state = 0
        self.glow_timer: Timer | None = None

    def on_mount(self) -> None:
        # Load CSS manually (fixes EXE crash)
        self.load_css(self.css_file)

        self.output.write("[bold bright_magenta]Welcome to Pantha Terminal.[/]")
        self.output.write("[magenta]Type 'help' to see available commands.[/]")
        self.output.write("")
        self.output.write("[dim]Tip: Press Ctrl+C to quit instantly.[/]")
        self.output.write("")

        self.glow_timer = self.set_interval(0.35, self.pulse_glow)
        self.query_one("#command_input", Input).focus()

    def compose(self) -> ComposeResult:
        with Vertical(id="frame", classes="glow1"):
            yield Static("💜 PANTHA TERMINAL 💜", id="header")

            self.output = RichLog(id="output", wrap=True, highlight=True, markup=True)
            yield self.output

            with Horizontal(id="inputbar"):
                yield Static("Pantha >", id="prompt")
                yield Input(placeholder="Type a command... (help)", id="command_input")

    def pulse_glow(self) -> None:
        frame = self.query_one("#frame")
        self.glow_state = (self.glow_state + 1) % 3

        frame.set_class(self.glow_state == 0, "glow1")
        frame.set_class(self.glow_state == 1, "glow2")
        frame.set_class(self.glow_state == 2, "glow3")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        command = event.value.strip()
        event.input.value = ""

        if not command:
            return

        self.output.write(f"[bold bright_magenta]Pantha >[/] {command}")

        result, action = run_command(command)

        if action == "clear":
            self.output.clear()
            return

        if action == "exit":
            await self.action_quit()
            return

        if result:
            self.output.write(result)

        self.output.write("")

    async def on_key(self, event: events.Key) -> None:
        if event.key == "ctrl+c":
            await self.action_quit()


if __name__ == "__main__":
    PanthaTerminal().run()
