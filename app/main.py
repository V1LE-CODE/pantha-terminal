import sys
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, RichLog, Input


def resource_path(relative: str) -> Path:
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    """
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative
    return Path(__file__).parent / relative


class PanthaTerminal(App):
    TITLE = "Pantha Terminal"
    SUB_TITLE = "Purple Glow • ASCII • Aesthetic"

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
        log.write("[b magenta]╔══════════════════════════════════╗[/]")
        log.write("[b magenta]║      🐆  Pantha Terminal  🐆      ║[/]")
        log.write("[b magenta]╚══════════════════════════════════╝[/]")
        log.write("[#b066ff]Welcome to Pantha Terminal.[/]")
        log.write("[#b066ff]Type something and press Enter.[/]\n")

        self.query_one("#input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        event.input.value = ""

        log = self.query_one("#log", RichLog)

        if not text:
            return

        log.write(f"[b #b066ff]pantha>[/] {text}")

        if text.lower() in ("exit", "quit"):
            self.exit()
            return

        if text.lower() == "clear":
            log.clear()
            return

        log.write(f"[#8f5bff]You typed:[/] {text}")

    def action_clear(self) -> None:
        self.query_one("#log", RichLog).clear()


if __name__ == "__main__":
    PanthaTerminal().run()
