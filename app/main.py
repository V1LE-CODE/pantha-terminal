from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Header, Footer, Static, Input, RichLog
from textual import events

ASCII_ART = r"""
██████╗  █████╗ ███╗   ██╗████████╗██╗  ██╗ █████╗
██╔══██╗██╔══██╗████╗  ██║╚══██╔══╝██║  ██║██╔══██╗
██████╔╝███████║██╔██╗ ██║   ██║   ███████║███████║
██╔═══╝ ██╔══██║██║╚██╗██║   ██║   ██╔══██║██╔══██║
██║     ██║  ██║██║ ╚████║   ██║   ██║  ██║██║  ██║
╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝
                 PANTHA TERMINAL
"""

class PanthaTerminal(App):
    CSS_PATH = "styles.tcss"
    TITLE = "Pantha Terminal"
    SUB_TITLE = "Purple Glow • ASCII • Aesthetic"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Vertical(id="root"):
            with Vertical(id="main_box"):
                yield Static("💜 Pantha Terminal", id="title")
                yield Static("Type commands below (try: help)", id="subtitle")

                yield Static(ASCII_ART, id="ascii")

                yield RichLog(id="log", wrap=True, highlight=True)

                with Vertical(id="input_row"):
                    yield Input(placeholder="Pantha > ", id="cmd")
                    yield Static("Tip: help | clear | exit", id="hint")

        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one("#log", RichLog)
        log.write("[b magenta]Pantha Terminal booted.[/]")
        log.write("[magenta]Ready for commands.[/]\n")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip()
        event.input.value = ""

        log = self.query_one("#log", RichLog)

        if not cmd:
            return

        log.write(f"[bold #ff00ff]Pantha >[/] {cmd}")

        if cmd.lower() in ["exit", "quit"]:
            log.write("[#c57dff]Closing Pantha Terminal...[/]")
            self.exit()
            return

        if cmd.lower() == "help":
            log.write("[#d8a7ff]Commands:[/]")
            log.write("  [#f4d6ff]help[/]  - show this menu")
            log.write("  [#f4d6ff]clear[/] - clear log")
            log.write("  [#f4d6ff]exit[/]  - close app")
            return

        if cmd.lower() == "clear":
            log.clear()
            return

        log.write(f"[#a96cff]Unknown command:[/] {cmd}")
        log.write("[#c57dff]Try: help[/]\n")


if __name__ == "__main__":
    PanthaTerminal().run()
