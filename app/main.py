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

from vault import Vault, VaultError, VaultLockedError

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
██████   █████  ███    ██ ████████ ██   ██  █████
██   ██ ██   ██ ████   ██    ██    ██   ██ ██   ██
██████  ███████ ██ ██  ██    ██    ███████ ███████ --  S E C U R E  N O T E  T E R M I N A L
██      ██   ██ ██  ██ ██    ██    ██   ██ ██   ██ ™ V1LE-CODE
██      ██   ██ ██   ████    ██    ██   ██ ██   ██
"""
        )

# --------------------------------------------------
# APP
# --------------------------------------------------

class PanthaTerminal(App):
    TITLE = "Pantha Terminal"
    SUB_TITLE = "Official Pantha Terminal v1.1.3"

    CSS = """
    Screen {
        background: #020005;
        color: #eadcff;
    }
    #log {
        background: #1a001f;
        color: #ffffff;
    }
    Input {
        background: #120017;
        color: #ffffff;
        border: round #ffffff;
    }
    #status_line {
        background: #120017;
        color: #00ff3c;
    }
    Header {
        background: #1a001f;
        color: #ffffff;
    }
    Footer {
        background: #1a001f;
        color: #ffffff;
    }
    """

    status_text: reactive[str] = reactive("Ready")

    def __init__(self) -> None:
        super().__init__()
        self.pantha_mode = False
        self.vault: Vault | None = None
        self.command_history: list[str] = []
        self.history_index = -1

        self.username = os.environ.get("USERNAME") or os.environ.get("USER") or "pantha"
        self.hostname = os.environ.get("COMPUTERNAME") or "local"

        self.load_history()

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
        log.write("[bold #a366ff]Pantha Terminal Online.[/]")
        log.write("[#7c33ff]Type [bold]unlock <password>[/] to start the vault.[/]")
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
            encoding="utf-8"
        )

    # --------------------------------------------------
    # SAFE COMMAND EXECUTION
    # --------------------------------------------------

    def run_command_safe(self, cmd: str) -> None:
        log = self.query_one("#log", RichLog)
        log.write(f"[#7c33ff]{self.username}@{self.hostname}[/] $ {escape(cmd)}")
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
        log = self.query_one("#log", RichLog)
        parts = shlex_split(cmd)
        if not parts:
            return

        low = parts[0].lower()

        # ----------------- VAULT UNLOCK -----------------
        if low == "unlock":
            if len(parts) < 2:
                log.write("[yellow]Usage: unlock <password>[/]")
                return
            self.vault = Vault(str(user_data_dir()))
            try:
                self.vault.unlock(parts[1])
                self.pantha_mode = True
                self.update_status("Vault Unlocked")
                log.write("[green]Vault unlocked.[/]")
            except VaultError:
                log.write("[red]Failed to unlock vault.[/]")
            return

        # ----------------- NOTE COMMANDS -----------------
        if low == "note":
            if not self.pantha_mode or not self.vault:
                log.write("[red]Vault locked. Use unlock first.[/]")
                return
            self.handle_note_command(parts)
            return

        # ----------------- EXIT -----------------
        if low in ("exit", "quit"):
            self.exit()
            return

        # ----------------- CLEAR -----------------
        if low == "clear":
            log.clear()
            self.update_status("Cleared")
            return

        log.write(f"[red]Unknown command:[/] {escape(cmd)}")

    # --------------------------------------------------
    # NOTE COMMANDS
    # --------------------------------------------------

    def handle_note_command(self, parts: list[str]):
        log = self.query_one("#log", RichLog)
        action = parts[1].lower() if len(parts) > 1 else ""

        if action == "list":
            notes = self.vault.list_notes()
            if not notes:
                log.write("[gray]No notes found.[/]")
                return
            log.write("[bold]Notes:[/]")
            for note_id, meta in notes.items():
                log.write(f"• {escape(meta['title'])} ({note_id[:8]})")
            return

        if action == "create":
            if len(parts) < 3:
                log.write("[yellow]Usage: note create <title>[/]")
                return
            title = parts[2]
            try:
                self.vault.create_note(title, "")
                log.write(f"[green]Created note:[/] {escape(title)}")
            except VaultError:
                log.write("[red]Failed to create note.[/]")
            return

        if action == "view":
            if len(parts) < 3:
                log.write("[yellow]Usage: note view <title>[/]")
                return
            title = parts[2]
            try:
                content = self.vault.read_note_by_title(title)
                log.write(f"[bold]{escape(title)}[/]\n{escape(content)}")
            except VaultError:
                log.write("[red]Note not found.[/]")
            return

        if action == "append":
            if len(parts) < 4:
                log.write("[yellow]Usage: note append <title> <text>[/]")
                return
            title, text = parts[2], " ".join(parts[3:])
            try:
                old = self.vault.read_note_by_title(title)
                new = old + "\n" + text
                self.vault.update_note_by_title(title, new)
                log.write(f"[green]Appended to note:[/] {escape(title)}")
            except VaultError:
                log.write("[red]Note not found.[/]")
            return

        if action == "delete":
            if len(parts) < 3:
                log.write("[yellow]Usage: note delete <title>[/]")
                return
            title = parts[2]
            try:
                self.vault.delete_note_by_title(title)
                log.write(f"[green]Deleted note:[/] {escape(title)}")
            except VaultError:
                log.write("[red]Note not found.[/]")
            return

        log.write("[yellow]Unknown note command.[/]")

    # --------------------------------------------------
    # STATUS
    # --------------------------------------------------

    def update_status(self, text: str) -> None:
        self.query_one("#status_line", Static).update(f"[#a366ff]STATUS:[/] {escape(text)}")

# --------------------------------------------------
# ENTRY
# --------------------------------------------------

if __name__ == "__main__":
    PanthaTerminal().run()
