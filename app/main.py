import sys
import asyncio
import traceback
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Input, RichLog
from textual import events
from textual.timer import Timer

from app.commands import run_command


def get_css_path() -> str:
    """
    CSS path that works in:
    - normal python runs
    - PyInstaller onefile EXE runs
    """
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

    def compose(self) -> ComposeResult:
        # Outer glow frame (pulses)
        with Vertical(id="outer_frame", classes="glow1"):
            # Inner frame (actual UI)
            with Vertical(id="inner_frame"):
                yield Static("💜 PANTHA TERMINAL 💜", id="header")

                # Splash (will hide after boot)
                with Vertical(id="splash_box"):
                    yield Static(PANTHA_LOGO, id="splash_logo")
                    yield Static("Booting Pantha systems...", id="splash_text")

                # Main UI (hidden during splash)
                self.output = RichLog(id="output", wrap=True, highlight=True, markup=True)
                yield self.output

                with Horizontal(id="inputbar"):
                    yield Static("Pantha >", id="prompt")
                    yield Input(placeholder="Type a command... (help)", id="command_input")

    async def on_mount(self) -> None:
        # Start glow pulse
        self.glow_timer = self.set_interval(0.28, self.pulse_glow)

        # Hide main UI during splash
        self.output.display = False
        self.query_one("#inputbar").display = False

        # Run splash boot sequence
        await self.splash_sequence()

        # Reveal main UI
        self.query_one("#splash_box").display = False
        self.output.display = True
        self.query_one("#inputbar").display = True

        self.output.write("[bold bright_magenta]Welcome to Pantha Terminal.[/]")
        self.output.write("[magenta]Type 'help' to see available commands.[/]")
        self.output.write("")
        self.output.write("[dim]Tip: Press Ctrl+C to quit instantly.[/]")
        self.output.write("")

        self.query_one("#command_input", Input).focus()

    async def splash_sequence(self) -> None:
        splash_text = self.query_one("#splash_text", Static)

        steps = [
            "Booting Pantha systems...",
            "Charging neon glow core...",
            "Linking terminal interface...",
            "Loading command modules...",
            "Boot complete 💜",
        ]

        for step in steps:
            splash_text.update(step)
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


def main():
    try:
        PanthaTerminal().run()
    except Exception:
        # If it crashes in EXE, show the error instead of closing instantly
        print("\n🔥 Pantha Terminal crashed!\n")
        print(traceback.format_exc())
        input("\nPress ENTER to close...")


if __name__ == "__main__":
    main()
