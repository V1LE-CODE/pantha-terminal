from __future__ import annotations

import os
import json
import traceback
from pathlib import Path
from shlex import split as shlex_split

from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual.reactive import reactive
from rich.markup import escape

# --------------------------------------------------
# USER DATA
# --------------------------------------------------

def user_data_dir() -> Path:
    path = Path.home() / ".pantha"
    path.mkdir(parents=True, exist_ok=True)
    return path

HISTORY_FILE = user_data_dir() / "history.json"


# --------------------------------------------------
# BANNER
# --------------------------------------------------

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
"""
        )


# --------------------------------------------------
# APP
# --------------------------------------------------

class PanthaTerminal(App):
    TITLE = "Pantha Terminal"
    SUB_TITLE = "Official Pantha Terminal v1.1.2"
    CSS_PATH = str(Path(__file__).parent.resolve() / "styles.tcss")

    status_text: reactive[str] = reactive("Ready")
    NOTES_FILE = user_data_dir() / "notes.json"

    def __init__(self) -> None:
        super().__init__()
        self.pantha_mode = False
        self.notes: dict[str, str] = {}
        self.command_history: list[str] = []
        self.history_index = -1

        self.username = os.environ.get("USERNAME") or os.environ.get("USER") or "pantha"
        self.hostname = os.environ.get("COMPUTERNAME") or "local"

        self.load_notes()
        self.load_history()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(id="header", show_clock=True)
        yield PanthaBanner(id="banner")

        with ScrollableContainer():
            yield RichLog(id="log", markup=True, wrap=True)

        yield Static("", id="status_line")
        yield Input(id="command_input", placeholder="Type a command...")
        yield Footer(id="footer")

    def on_mount(self) -> None:
        log = self.query_one("#log", RichLog)
        log.write("[bold purple]Pantha Terminal Online.[/]")
        log.write("[#b066ff]Type [bold]pantham[/] to awaken the core.[/]")
        self.focus_input()

    # --------------------------------------------------
    # INPUT / HOTKEYS
    # --------------------------------------------------

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd = event.value.strip()
        event.input.value = ""
        self.run_command_safe(cmd)
        self.focus_input()

    def on_key(self, event) -> None:
        log = self.query_one("#log", RichLog)

        if event.key == "ctrl+l":
            log.clear()
            self.update_status("Cleared")
            event.stop()
            return

        if event.key == "ctrl+c":
            self.exit()

        # Up/Down history navigation
        inp = self.query_one("#command_input", Input)
        if event.key == "up" and self.command_history:
            self.history_index = max(0, self.history_index - 1)
            inp.value = self.command_history[self.history_index]
            inp.cursor_position = len(inp.value)
            event.stop()
        if event.key == "down" and self.command_history:
            self.history_index = min(len(self.command_history), self.history_index + 1)
            inp.value = "" if self.history_index >= len(self.command_history) else self.command_history[self.history_index]
            inp.cursor_position = len(inp.value)
            event.stop()

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
    # HISTORY
    # --------------------------------------------------

    def load_history(self) -> None:
        try:
            if HISTORY_FILE.exists():
                self.command_history = json.loads(HISTORY_FILE.read_text("utf-8"))
            else:
                self.command_history = []
        except Exception:
            self.command_history = []

    def save_history(self) -> None:
        HISTORY_FILE.write_text(
            json.dumps(self.command_history, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # --------------------------------------------------
    # SAFE COMMAND EXECUTION
    # --------------------------------------------------

    def run_command_safe(self, cmd: str) -> None:
        log = self.query_one("#log", RichLog)
        log.write(f"[#b066ff]{self.username}@{self.hostname}[/] $ {escape(cmd)}")

        try:
            self.command_history.append(cmd)
            self.history_index = len(self.command_history)
            self.save_history()
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

        if low == "clear":
            log.clear()
            self.update_status("Cleared")
            return

        log.write(f"[red]Unknown command:[/] {escape(cmd)}")

    # --------------------------------------------------
    # STATUS
    # --------------------------------------------------

    def update_status(self, text: str) -> None:
        self.query_one("#status_line", Static).update(
            f"[purple]STATUS:[/] {escape(text)}"
        )

    # --------------------------------------------------
    # NOTES COMMANDS
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
        try:
            parts = shlex_split(cmd)
        except Exception:
            log.write("[red]Failed to parse command.[/]")
            return

        if len(parts) < 2:
            log.write("[yellow]Usage: note list|create|view|append|delete|rename|search|export|import[/]")
            return

        action = parts[1].lower()

        # Handle all note actions
        if action == "list":
            if not self.notes:
                log.write("[gray]No notes found.[/]")
                return
            log.write("[bold]Notes:[/]")
            for t in self.notes:
                log.write(f"• {escape(t)}")
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

        if action == "append":
            if len(parts) < 4:
                log.write("[yellow]note append <title> <text>[/]")
                return
            title, text = parts[2], " ".join(parts[3:])
            if title not in self.notes:
                log.write("[red]Note not found.[/]")
                return
            self.notes[title] += "\n" + text
            self.save_notes()
            log.write(f"[green]Appended to note:[/] {escape(title)}")
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

        if action == "rename":
            if len(parts) < 4:
                log.write("[yellow]note rename <old> <new>[/]")
                return
            old, new = parts[2], parts[3]
            if old not in self.notes:
                log.write("[red]Note not found.[/]")
                return
            if new in self.notes:
                log.write("[red]A note with that name already exists.[/]")
                return
            self.notes[new] = self.notes.pop(old)
            self.save_notes()
            log.write(f"[green]Renamed note:[/] {escape(old)} → {escape(new)}")
            return

        log.write("[yellow]Unknown note command.[/]")

    # --------------------------------------------------
    # PANTHAM ASCII
    # --------------------------------------------------

    def show_pantha_ascii(self) -> None:
        ascii_art = r"""
(\ 
\'\ 
 \'\     __________  
 / '|   ()_________)
 \ '/    \ ~~~~~~~~ \
   \       \ ~~~~~~   \
   ==).      \__________\
  (__)       ()__________)⠀⠀⠀⠀⠀ 
"""
        log = self.query_one("#log", RichLog)
        log.write(f"[bold purple]{ascii_art}[/]")


# --------------------------------------------------
# ENTRY
# --------------------------------------------------

if __name__ == "__main__":
    PanthaTerminal().run()
