from __future__ import annotations

import os
import sys
import json
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual.reactive import reactive


# --------------------------------------------------
# RESOURCE PATH (PYINSTALLER SAFE)
# --------------------------------------------------

def resource_path(relative: str) -> str:
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative)


# --------------------------------------------------
# BANNER
# --------------------------------------------------

class PanthaBanner(Static):
    def on_mount(self) -> None:
        self.update(
            r"""
     ^---^
    ( . . )
    (___'_)
v1  ( | | )___
   (__m_m__)__}
██████╗  █████╗ ███╗   ██╗████████╗██╗  ██╗ █████╗
██╔══██╗██╔══██╗████╗  ██║╚══██╔══╝██║  ██║██╔══██╗
██████╔╝███████║██╔██╗ ██║   ██║   ███████║███████║
██╔═══╝ ██╔══██║██║╚██╗██║   ██║   ██╔══██║██╔══██║
██║     ██║  ██║██║ ╚████║   ██║   ██║  ██║██║  ██║
╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝

        ░▒▓█▓▒░  P A N T H A   T E R M I N A L  ░▒▓█▓▒░
"""
        )


# --------------------------------------------------
# APP
# --------------------------------------------------

class PanthaTerminal(App):
    TITLE = "Pantha Terminal"
    SUB_TITLE = "Official Pantha Terminal V1.0.0"

    CSS_PATH = None
    status_text: reactive[str] = reactive("Ready")

    NOTES_FILE = Path(__file__).parent / "notes.json"

    def __init__(self) -> None:
        super().__init__()

        self.command_history: list[str] = []
        self.history_index = -1
        self.pantha_mode = False

        self.username = os.environ.get("USERNAME") or os.environ.get("USER") or "pantha"
        self.hostname = (
            os.environ.get("COMPUTERNAME")
            or (os.uname().nodename if hasattr(os, "uname") else "local")
        )

        self.notes: dict[str, str] = {}
        self.load_notes()

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
                            "• Notes Enabled\n"
                            "• Purple Aesthetic",
                            id="system_info",
                        )

                        yield Static("COMMANDS", id="panel_title2")
                        yield Static(
                            "note list\n"
                            "note create <title>\n"
                            "note view <title>\n"
                            "note write <title> <text>\n"
                            "note delete <title>",
                            id="hotkeys",
                        )

                    with Vertical(id="right_panel"):
                        yield Static("OUTPUT", id="output_title")

                        with ScrollableContainer(id="log_wrap"):
                            yield RichLog(id="log", highlight=True, markup=True, wrap=True)

                        yield Static("", id="status_line")
                        yield Input(
                            placeholder="Type a command...",
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
        log.write("[#b066ff]Notes system initialized.[/]")
        self.update_status("Ready")

        self.query_one("#command_input", Input).focus()

    # --------------------------------------------------
    # INPUT
    # --------------------------------------------------

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip()
        event.input.value = ""
        self.run_command(cmd)

    # --------------------------------------------------
    # STATUS
    # --------------------------------------------------

    def update_status(self, text: str) -> None:
        self.status_text = text
        self.query_one("#status_line", Static).update(
            f"[#ff4dff]STATUS:[/] [#ffffff]{text}[/]"
        )

    def prompt(self) -> str:
        return f"[#b066ff]{self.username}[/]@[#ff4dff]{self.hostname}[/]:[#ffffff]~$[/]"

    # --------------------------------------------------
    # NOTES
    # --------------------------------------------------

    def load_notes(self) -> None:
        if self.NOTES_FILE.exists():
            try:
                with open(self.NOTES_FILE, "r", encoding="utf-8") as f:
                    self.notes = json.load(f)
            except Exception:
                self.notes = {}
        else:
            self.notes = {}

    def save_notes(self) -> None:
        with open(self.NOTES_FILE, "w", encoding="utf-8") as f:
            json.dump(self.notes, f, indent=2, ensure_ascii=False)

    def handle_note_command(self, args: list[str]) -> None:
        log = self.query_one("#log", RichLog)

        if not args:
            log.write("[yellow]Usage: note [list|create|view|write|delete][/]")
            return

        action = args[0].lower()

        if action == "list":
            if not self.notes:
                log.write("[gray]No notes found.[/]")
                return
            log.write("[bold]Notes:[/]")
            for title in self.notes:
                log.write(f"• {title}")
            return

        if action == "create":
            title = " ".join(args[1:])
            if not title:
                log.write("[yellow]note create <title>[/]")
                return
            if title in self.notes:
                log.write(f"[red]Note '{title}' already exists.[/]")
                return
            self.notes[title] = ""
            self.save_notes()
            log.write(f"[green]Created note '{title}'.[/]")
            return

        if action == "view":
            title = " ".join(args[1:])
            if title not in self.notes:
                log.write(f"[red]Note '{title}' not found.[/]")
                return
            content = self.notes[title] or "[gray]<empty>[/]"
            log.write(f"[bold]{title}[/]\n{content}")
            return

        if action == "write":
            if len(args) < 3:
                log.write("[yellow]note write <title> <text>[/]")
                return
            title = args[1]
            text = " ".join(args[2:])
            if title not in self.notes:
                log.write(f"[red]Note '{title}' not found.[/]")
                return
            self.notes[title] = text
            self.save_notes()
            log.write(f"[green]Updated note '{title}'.[/]")
            return

        if action == "delete":
            title = " ".join(args[1:])
            if title not in self.notes:
                log.write(f"[red]Note '{title}' not found.[/]")
                return
            del self.notes[title]
            self.save_notes()
            log.write(f"[green]Deleted note '{title}'.[/]")
            return

        log.write(f"[yellow]Unknown note command: {action}[/]")

    # --------------------------------------------------
    # COMMAND ROUTER
    # --------------------------------------------------

    def run_command(self, cmd: str) -> None:
        if not cmd:
            return

        self.command_history.append(cmd)
        self.history_index = len(self.command_history)

        log = self.query_one("#log", RichLog)
        log.write(f"{self.prompt()} [#ffffff]{cmd}[/]")

        low = cmd.lower()

        if low.startswith("note"):
            self.handle_note_command(cmd.split()[1:])
            return

        if low == "clear":
            log.clear()
            self.update_status("Cleared")
            return

        if low in ("exit", "quit"):
            self.exit()
            return

        log.write(f"[red]Unknown command: {cmd}[/]")


# --------------------------------------------------
# ENTRY
# --------------------------------------------------

if __name__ == "__main__":
    PanthaTerminal().run()
