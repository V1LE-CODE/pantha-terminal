import sys
import asyncio
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Input, RichLog
from textual import events
from textual.timer import Timer

from app.commands import run_command


def get_css_path() -> str:
    """CSS path that works in normal runs + PyInstaller EXE."""
    if hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
        return str(base / "styles.tcss")
    return str(Path(__file__).with_name("styles.tcss"))


PANTHA_LOGO = r"""
██████╗  █████╗ ███╗   ██╗████████╗██╗  ██╗ █████╗
██╔══██╗██╔══██╗████╗  ██║╚══██╔══╝██║  ██║██╔══██╗
██████╔╝███████║██╔██╗ ██║   ██║   ███████║███████║
██╔═══╝ ██╔══██║██║╚██╗██║   ██║   ██╔══██║██╔══██║
██║     ██║  ██║██║ ╚████║   ██║   ██║  ██║██║  ██║
╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝
"""


class PanthaTerminal(App):
    TITLE = "Pantha Terminal"
    SUB_TITLE = "Neon Purple Terminal UI"
    CSS_PATH = get_css_path()

    def __init__(self):
        super().__init__()
        self.glow_state = 0
        self.glow_timer: Timer | None = None

        self.showing_splash = True

    def compose(self) -> ComposeResult:
        # OUTER glow frame
        with Vertical(id="outer_frame", classes="glow1"):
            # INNER frame (real UI)
            with Vertical(id="inner_frame"):
                yield Static("💜 PANTHA TERMINAL 💜", id="header")

                # Splash screen container (we will hide later)
                with Vertical(id="splash_box"):
                    yield Static(PANTHA_LOGO, id="splash_logo")
                    yield Static("Loading neon systems...", id="splash_text")

                # Main output + input (hidden during splash)
                self.output = RichLog(id="output", wrap=True, highlight=True, markup=True)
                yield self.output

                with Horizontal(id="inputbar"):
                    yield Static("Pantha >", id="prompt")
                    yield Input(placeholder="Type a command... (help)", id="command_input")

    async def on_mount(self) -> None:
        # Start glow pulse
        self.glow_timer = self.set_interval(0.30, self.pulse_glow)

        # Hide main UI first (until splash done)
        self.output.display = False
        self.query_one("#inputbar").display = False

        # Run splash animation then reveal UI
        await self.run_splash()

        self.output.display = True
        self.query_one("#inputbar").display = True
        self.query_one("#splash_box").display = False

        self.output.write("[bold bright_magenta]Welcome to Pantha Terminal.[/]")
        self.output.write("[magenta]Type 'help' to see available commands.[/]")
        self.output.write("")
        self.output.write("[dim]Tip: Press Ctrl+C to quit instantly.[/]")
        self.output.write("")

        self.query_one("#command_input", Input).focus()

    async def run_splash(self) -> None:
        splash_text = self.query_one("#splash_text", Static)

        steps = [
            "Loading neon systems...",
            "Charging purple glow core...",
            "Linking Pantha interface...",
            "Boot complete. Welcome 💜",
        ]

        for s in steps:
            splash_text.update(s)
            await asyncio.sleep(0.55)

    def pulse_glow(self) -> None:
        outer = self.query_one("#outer_frame")
        self.glow_state = (self.glow_state + 1) % 3

        outer.set_class(self.glow_state == 0, "glow1")
        outer.set_class(self.glow_state == 1, "glow2")
        outer.set_class(self.glow_state == 2, "glow3")

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
