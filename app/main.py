from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual.reactive import reactive
from textual import events


def resource_path(relative: str) -> str:
    try:
        base_path = sys._MEIPASS  # type: ignore
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative)


class PanthaBanner(Static):
    def on_mount(self) -> None:
        self.update(
            """
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
    SUB_TITLE = "Purple ASCII Terminal"
    status_text: reactive[str] = reactive("Ready")

    def load_tcss(self) -> None:
        path = Path(resource_path("app/styles.tcss"))
        self.stylesheet.read(path)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Vertical(id="root", classes="boot-init"):
            yield PanthaBanner(id="banner")

            with Horizontal(id="main_row"):
                with Vertical(id="left_panel"):
                    yield Static("SYSTEM", id="panel_title")
                    yield Static(
                        f"• User: {os.getenv('USERNAME','pantha')}\n"
                        f"• Host: local\n"
                        "• Pantha Terminal\n"
                        "• Textual UI\n"
                        "• Purple Glow\n"
                        "• ASCII Mode",
                        id="system_info",
                    )

                    yield Static("HOTKEYS", id="panel_title2")
                    yield Static(
                        "ENTER → run command\n"
                        "UP/DOWN → history\n"
                        "CTRL+C → quit\n"
                        "CTRL+L → clear log",
                        id="hotkeys",
                    )

                with Vertical(id="right_panel"):
                    yield Static("OUTPUT", id="output_title")

                    with ScrollableContainer(id="log_wrap"):
                        yield RichLog(id="log", highlight=True, markup=True)

                    yield Static("", id="status_line")
                    yield Input(placeholder="Type a command...", id="command_input")

        yield Footer()

    async def on_mount(self) -> None:
        self.load_tcss()

        root = self.query_one("#root")
        root.remove_class("boot-init")
        root.add_class("boot-glow")
        await self.sleep(0.15)
        root.remove_class("boot-glow")
        root.add_class("boot-ready")

        log = self.query_one("#log", RichLog)
        log.write("[bold #ff4dff]Pantha Terminal Online[/]")
        log.write("[#b066ff]Type help for commands[/]")

        self.query_one("#command_input").focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        inp = event.input
        cmd = inp.value.strip()
        inp.value = ""

        inp.add_class("command-fired")
        await self.sleep(0.08)
        inp.remove_class("command-fired")

        if cmd:
            self.query_one("#log", RichLog).write(f"[#b066ff]$ {cmd}[/]")

    def on_key(self, event: events.Key) -> None:
        if event.key == "ctrl+l":
            self.query_one("#log", RichLog).clear()
