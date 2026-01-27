from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual.reactive import reactive


def resource_path(relative: str) -> str:
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative)


class PanthaBanner(Static):
    def on_mount(self) -> None:
        self.update(
            r"""
██████╗  █████╗ ███╗   ██╗████████╗██╗  ██╗ █████╗
██╔══██╗██╔══██╗████╗  ██║╚══██╔══╝██║  ██║██╔══██╗
██████╔╝███████║██╔██╗ ██║   ██║   ███████║███████║
██╔═══╝ ██╔══██║██║╚██╗██║   ██║   ██╔══██║██╔══██║
██║     ██║  ██║██║ ╚████║   ██║   ██║  ██║██║  ██║
╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝

        ░▒▓█▓▒░  P A N T H A   T E R M I N A L  ░▒▓█▓▒░
"""
        )


class PanthaTerminal(App):
    TITLE = "Pantha Terminal"
    SUB_TITLE = "Official Pantha Terminal V0.0.0"

    CSS_PATH = None
    status_text: reactive[str] = reactive("Ready")

    def __init__(self) -> None:
        super().__init__()
        self.command_history: list[str] = []
        self.history_index = -1

        self.username = os.environ.get("USERNAME") or os.environ.get("USER") or "pantha"
        self.hostname = (
            os.environ.get("COMPUTERNAME")
            or (os.uname().nodename if hasattr(os, "uname") else "local")
        )

    # --------------------------------------------------
    # STYLES
    # --------------------------------------------------

    def load_tcss(self) -> None:
        dev = Path(__file__).parent / "styles.tcss"
        if dev.exists():
            self.stylesheet.read(dev)
            return

        packed = Path(resource_path("app/styles.tcss"))
        if packed.exists():
            self.stylesheet.read(packed)

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def compose(self) -> ComposeResult:
        with Vertical(id="frame"):
            yield Header(show_clock=True)

            with Vertical(id="root"):
                yield PanthaBanner(id="banner")

                with Horizontal(id="main_row"):
                    with Vertical(id="left_panel"):
                        yield Static("SYSTEM", id="panel_title")
                        yield Static(
                            f"• User: {self.username}\n"
                            f"• Host: {self.hostname}\n"
                            "• Pantha Terminal\n"
                            "• Your GO-TO Terminal\n"
                            "• Purple Aesthetic\n"
                            "• ASCII / Pantha Mode",
                            id="system_info",
                        )

                        yield Static("HOTKEYS", id="panel_title2")
                        yield Static(
                            "ENTER   → run command\n"
                            "UP/DOWN → history\n"
                            "CTRL+C  → quit\n"
                            "CTRL+L  → clear log",
                            id="hotkeys",
                        )

                    with Vertical(id="right_panel"):
                        yield Static("OUTPUT", id="output_title")

                        with ScrollableContainer(id="log_wrap"):
                            yield RichLog(id="log", highlight=True, markup=True, wrap=True)

                        yield Static("", id="status_line")
                        yield Input(
                            placeholder="Type a command... (try: help)",
                            id="command_input",
                        )

            yield Footer()

    # --------------------------------------------------
    # LIFECYCLE
    # --------------------------------------------------

    def on_mount(self) -> None:
        self.load_tcss()

        log = self.query_one("#log", RichLog)
        log.write("[bold #ff4dff]Pantha Terminal Online.[/]")
        log.write("[#b066ff]Type [bold]help[/] for commands.[/]")
        log.write("[#b066ff]Try [bold]ascii[/] to enable pantha mode.[/]")
        self.update_status("Ready")

        self.query_one("#command_input", Input).focus()

    # --------------------------------------------------
    # INPUT HANDLING  ✅ FIX
    # --------------------------------------------------

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip()
        event.input.value = ""
        self.run_command(cmd)

    def on_key(self, event) -> None:
        inp = self.query_one("#command_input", Input)

        if event.key == "ctrl+l":
            self.query_one("#log", RichLog).clear()
            self.update_status("Cleared")
            event.stop()
            return

        if event.key == "up" and self.command_history:
            self.history_index = max(0, self.history_index - 1)
            inp.value = self.command_history[self.history_index]
            inp.cursor_position = len(inp.value)
            event.stop()
            return

        if event.key == "down" and self.command_history:
            self.history_index = min(len(self.command_history), self.history_index + 1)
            inp.value = "" if self.history_index >= len(self.command_history) else self.command_history[self.history_index]
            inp.cursor_position = len(inp.value)
            event.stop()
            return

    # --------------------------------------------------
    # COMMANDS
    # --------------------------------------------------

    def update_status(self, text: str) -> None:
        self.status_text = text
        self.query_one("#status_line", Static).update(
            f"[#ff4dff]STATUS:[/] [#ffffff]{text}[/]"
        )

    def prompt(self) -> str:
        return f"[#b066ff]{self.username}[/]@[#ff4dff]{self.hostname}[/]:[#ffffff]~$[/]"

    def run_command(self, cmd: str) -> None:
        if not cmd:
            return

        self.command_history.append(cmd)
        self.history_index = len(self.command_history)

        log = self.query_one("#log", RichLog)
        log.write(f"{self.prompt()} [#ffffff]{cmd}[/]")

        low = cmd.lower()

        if low == "clear":
            log.clear()
            self.update_status("Cleared")
            return

        if low == "ascii":
            self.show_ascii()
            self.update_status("ASCII shown")
            return

        if low in ("exit", "quit"):
            self.exit()
            return

        self.run_shell(cmd)

    def run_shell(self, cmd: str) -> None:
        log = self.query_one("#log", RichLog)
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            for line in result.stdout.splitlines():
                log.write(f"[#ffffff]{line}[/]")
            for line in result.stderr.splitlines():
                log.write(f"[bold red]{line}[/]")
            self.update_status("Command executed")
        except Exception as e:
            log.write(f"[bold red]{e}[/]")

    def show_ascii(self) -> None:
        self.query_one("#log", RichLog).write(
            "[bold #ff4dff]\nPANTHA MODE ENABLED\n[/]"
        )


if __name__ == "__main__":
    PanthaTerminal().run()
