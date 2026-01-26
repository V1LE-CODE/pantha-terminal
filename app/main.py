import sys
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, RichLog, Input


def resource_path(relative: str) -> Path:
    """
    Works for normal runs + PyInstaller builds.
    """
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative
    return Path(__file__).parent / relative


class PanthaTerminal(App):
    TITLE = "Pantha Terminal"
    SUB_TITLE = "Purple Glow • ASCII Terminal"

    CSS_PATH = resource_path("styles.tcss")

    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+l", "clear", "Clear"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="root"):
            yield RichLog(id="log", highlight=True, markup=True)
            yield Input(placeholder="Type a command…", id="input")
        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one("#log", RichLog)

        log.write("[b #b066ff]╔══════════════════════════════════════╗[/]")
        log.write("[b #b066ff]║      🐆   PANTHA TERMINAL   🐆       ║[/]")
        log.write("[b #b066ff]╚══════════════════════════════════════╝[/]")
        log.write("[#ff4dff]Neon Purple Mode: ONLINE[/]")
        log.write("[#8f5bff]Type a command and press Enter.[/]\n")

        self.query_one("#input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip()
        event.input.value = ""

        log = self.query_one("#log", RichLog)

        if not cmd:
            return

        log.write(f"[b #b066ff]pantha>[/] {cmd}")

        if cmd.lower() in ("exit", "quit"):
            self.exit()
            return

        if cmd.lower() == "clear":
            log.clear()
            return

        log.write(f"[#8f5bff]Echo:[/] {cmd}")

    def action_clear(self) -> None:
        self.query_one("#log", RichLog).clear()


if __name__ == "__main__":
    PanthaTerminal().run()
