from __future__ import annotations

import os
import json
import traceback
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual.reactive import reactive
from rich.markup import escape


# --------------------------------------------------
# USER DATA PATH (SAFE + WRITABLE)
# --------------------------------------------------

def user_data_dir() -> Path:
    path = Path.home() / ".pantha"
    path.mkdir(parents=True, exist_ok=True)
    return path


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
    SUB_TITLE = "Official Pantha Terminal v1.0.0"

    status_text: reactive[str] = reactive("Ready")
    NOTES_FILE = user_data_dir() / "notes.json"

    def __init__(self) -> None:
        super().__init__()

        self.pantha_mode = False
        self.notes: dict[str, str] = {}

        self.username = os.environ.get("USERNAME") or os.environ.get("USER") or "pantha"
        self.hostname = os.environ.get("COMPUTERNAME") or "local"

        self.load_notes()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield PanthaBanner()
        with ScrollableContainer():
            yield RichLog(id="log", markup=True, wrap=True)
        yield Static("", id="status_line")
        yield Input(id="command_input", placeholder="Type a command...")
        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one("#log", RichLog)
        log.write("[bold #ff4dff]Pantha Terminal Online.[/]")
        log.write("[#b066ff]Type [bold]pantham[/] to awaken the core.[/]")
        self.focus_input()

    # --------------------------------------------------
    # INPUT
    # --------------------------------------------------

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip()
        event.input.value = ""
        self.run_command_safe(cmd)
        self.focus_input()

    def focus_input(self) -> None:
        self.query_one("#command_input", Input).focus()

    # --------------------------------------------------
    # NOTES STORAGE
    # --------------------------------------------------

    def load_notes(self) -> None:
        try:
            if self.NOTES_FILE.exists():
                self.notes = json.loads(self.NOTES_FILE.read_text("utf-8"))
            else:
                self.notes = {}
                self.save_notes()
        except Exception:
            self.notes = {}

    def save_notes(self) -> None:
        self.NOTES_FILE.write_text(
            json.dumps(self.notes, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # --------------------------------------------------
    # SAFE COMMAND EXECUTION
    # --------------------------------------------------

    def run_command_safe(self, cmd: str) -> None:
        log = self.query_one("#log", RichLog)
        log.write(f"[#b066ff]{self.username}@{self.hostname}[/] $ {escape(cmd)}")

        try:
            self.run_command(cmd)
        except Exception:
            log.write("[bold red]INTERNAL ERROR[/]")
            log.write(escape(traceback.format_exc()))

    # --------------------------------------------------
    # COMMAND ROUTER
    # --------------------------------------------------

    def run_command(self, cmd: str) -> None:
        low = cmd.lower()
        log = self.query_one("#log", RichLog)

        if low == "pantham":
            self.pantha_mode = True
            self.show_pantha_ascii()
            self.update_status("PANTHAM MODE ONLINE")
            return

        if low == "pantham off":
            self.pantha_mode = False
            log.write("[gray]Pantham disengaged.[/]")
            self.update_status("PANTHAM MODE OFF")
            return

        if low.startswith("note"):
            self.handle_note_command(cmd)
            return

        if low in ("exit", "quit"):
            self.exit()
            return

        log.write(f"[red]Unknown command:[/] {escape(cmd)}")

    # --------------------------------------------------
    # STATUS
    # --------------------------------------------------

    def update_status(self, text: str) -> None:
        self.status_text = text
        self.query_one("#status_line", Static).update(
            f"[#ff4dff]STATUS:[/] {escape(text)}"
        )

    # --------------------------------------------------
    # NOTES
    # --------------------------------------------------

    def require_pantha(self) -> bool:
        if not self.pantha_mode:
            self.query_one("#log", RichLog).write(
                "[red]Notes locked. Enter [bold]pantham[/] first.[/]"
            )
            return False
        return True

    def handle_note_command(self, cmd: str) -> None:
        if not self.require_pantha():
            return

        log = self.query_one("#log", RichLog)
        parts = cmd.split(maxsplit=2)

        if len(parts) < 2:
            log.write("[yellow]Usage: note list|create|view|write|delete[/]")
            return

        action = parts[1].lower()

        if action == "list":
            if not self.notes:
                log.write("[gray]No notes found.[/]")
                return
            log.write("[bold]Notes:[/]")
            for title in self.notes:
                log.write(f"• {escape(title)}")
            return

        if action == "create":
            if len(parts) < 3:
                log.write("[yellow]note create <title>[/]")
                return
            title = parts[2]
            if title in self.notes:
                log.write("[red]Note already exists.[/]")
                return
            self.notes[title] = ""
            self.save_notes()
            log.write(f"[green]Created note:[/] {escape(title)}")
            return

        if action == "view":
            title = parts[2]
            if title not in self.notes:
                log.write("[red]Note not found.[/]")
                return
            content = escape(self.notes[title]) or "[gray]<empty>[/]"
            log.write(f"[bold]{escape(title)}[/]\n{content}")
            return

        if action == "delete":
            title = parts[2]
            if title not in self.notes:
                log.write("[red]Note not found.[/]")
                return
            del self.notes[title]
            self.save_notes()
            log.write(f"[green]Deleted note:[/] {escape(title)}")
            return

        if action == "write":
            if " " not in parts[2]:
                log.write("[yellow]note write <title> <text>[/]")
                return
            title, text = parts[2].split(" ", 1)
            if title not in self.notes:
                log.write("[red]Note not found.[/]")
                return
            self.notes[title] = text
            self.save_notes()
            log.write(f"[green]Updated note:[/] {escape(title)}")
            return

        log.write("[yellow]Unknown note command.[/]")

    # --------------------------------------------------
    # PANTHAM ASCII
    # --------------------------------------------------

    def show_pantha_ascii(self) -> None:
        ascii_art = r"""
⠀⠀⠀⠀⠀⠀⠀/\_/\ 
   ____/ o o \
 /~____  =ø= /
(______)__m_m)
██████╗  █████╗ ███╗   ██╗████████╗██╗  ██╗ █████╗ ███╗   ███╗
██╔══██╗██╔══██╗████╗  ██║╚══██╔══╝██║  ██║██╔══██╗████╗ ████║
██████╔╝███████║██╔██╗ ██║   ██║   ███████║███████║██╔████╔██║
██╔═══╝ ██╔══██║██║╚██╗██║   ██║   ██╔══██║██╔══██║██║╚██╔╝██║
██║     ██║  ██║██║ ╚████║   ██║   ██║  ██║██║  ██║██║ ╚═╝ ██║
╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝

      ░▒▓█▓▒░  P A N T H A M   A W A K E N E D  ░▒▓█▓▒░
"""
        self.query_one("#log", RichLog).write(f"[bold #ff4dff]{ascii_art}[/]")


# --------------------------------------------------
# ENTRY
# --------------------------------------------------

if __name__ == "__main__":
    PanthaTerminal().run()
