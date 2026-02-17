from __future__ import annotations
import os
import json
import time
import uuid
import traceback
from pathlib import Path
from shlex import split as shlex_split
from typing import Dict, Optional

from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Header, Input, Static, RichLog
from textual.reactive import reactive
from rich.markup import escape

from vault import Vault, VaultError

# =========================================================
# PATH CONFIGURATION
# =========================================================
def user_data_dir() -> Path:
    path = Path.home() / ".pantha"
    path.mkdir(parents=True, exist_ok=True)
    return path

DATA_DIR = user_data_dir()
HISTORY_FILE = DATA_DIR / "history.json"
PIN_FILE = DATA_DIR / "pins.json"

# =========================================================
# ASCII BANNER
# =========================================================
class PanthaBanner(Static):
    def on_mount(self) -> None:
        self.update(r"""
██████   █████  ███    ██ ████████ ██   ██  █████
██   ██ ██   ██ ████   ██    ██    ██   ██ ██   ██
██████  ███████ ██ ██  ██    ██    ███████ ███████      --  ENCRYPTED & SECURE NOTE-BASED TERMINAL
██      ██   ██ ██  ██ ██    ██    ██   ██ ██   ██                 BROUGHT TO YOU BY:  ™ V1LE-CODE
██      ██   ██ ██   ████    ██    ██   ██ ██   ██
""")

# =========================================================
# STATUS BAR
# =========================================================
class StatusBar(Static):
    def set(self, text: str):
        self.update(f" STATUS ▸ {text} ")

# =========================================================
# TERMINAL APPLICATION
# =========================================================
class PanthaTerminal(App):

    SUB_TITLE = "Official Pantha Terminal v1.5.0"
    ENABLE_COMMAND_PALETTE = False

    CSS = """
    Screen { background: #020005; color: #eadcff; }
    Header { background: #1a001f; }
    #log { background: #1a001f; }
    Input { background: #120017; border: round #aa00ff; }
    #statusbar { dock: bottom; height: 1; background: #120017; color: #00ff9c; content-align: left middle; }
    """

    BINDINGS = [
        ("ctrl+l", "clear_log", "Clear"),
        ("ctrl+q", "quit_app", "Quit"),
        ("ctrl+i", "focus_input", "Focus"),
        ("ctrl+n", "list_notes", "Notes"),
        ("ctrl+f", "search_notes", "Search"),
        ("up", "history_prev", ""),
        ("down", "history_next", ""),
    ]

    status_text: reactive[str] = reactive("Ready")

    # =====================================================
    # INIT
    # =====================================================
    def __init__(self):
        super().__init__()
        self.vault: Vault = Vault(str(DATA_DIR))
        self.pantha_mode = False
        self.command_history: list[str] = []
        self.history_index = -1
        self.pins: set[str] = set()
        self.awaiting_password_input = False
        self.awaiting_password_setup = False
        self._first_pass: Optional[str] = None

        self.username = os.environ.get("USERNAME") or os.environ.get("USER") or "pantha"
        self.hostname = os.environ.get("COMPUTERNAME") or "local"

        self.load_history()
        self.load_pins()
        self.update_header()

    # =====================================================
    # HEADER & STATUS
    # =====================================================
    def update_header(self):
        lock_icon = "🔓" if self.pantha_mode else "🔒"
        self.title = f"{lock_icon} Pantha Terminal"

    def update_status(self, text: str):
        self.query_one("#statusbar", StatusBar).set(text)

    # =====================================================
    # COMPOSE UI
    # =====================================================
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield PanthaBanner()
        with ScrollableContainer():
            yield RichLog(id="log", markup=True, wrap=True)
        yield Input(id="command_input", placeholder="Enter command...")
        yield StatusBar(id="statusbar")

    def on_mount(self):
        self.log = self.query_one("#log", RichLog)
        self.input_widget = self.query_one("#command_input", Input)
        self.focus_input()
        self.show_password_prompt()

    def focus_input(self):
        self.input_widget.focus()

    # =====================================================
    # PASSWORD PROMPT
    # =====================================================
    def show_password_prompt(self):
        """Prompt user for password first"""
        if not self.vault.has_password():
            self.log.write("[bold yellow]No vault password set.[/]")
            self.log.write("[bold yellow]Please create a new password:[/]")
            self.awaiting_password_setup = True
        else:
            self.log.write("[bold cyan]Enter vault password to unlock:[/]")
            self.awaiting_password_input = True

    def on_input_submitted(self, event: Input.Submitted):
        text = event.value.strip()
        event.input.value = ""
        if self.awaiting_password_input:
            try:
                self.vault.unlock(text)
                self.pantha_mode = True
                self.update_header()
                self.update_status("Vault Unlocked")
                self.log.write("[green]Vault unlocked successfully![/]")
                self.awaiting_password_input = False
            except VaultError:
                self.log.write("[red]Wrong password, try again.[/]")
        elif self.awaiting_password_setup:
            if not self._first_pass:
                self._first_pass = text
                self.log.write("[bold cyan]Confirm new password:[/]")
            else:
                if text != self._first_pass:
                    self.log.write("[red]Passwords do not match. Try again.[/]")
                    self._first_pass = None
                else:
                    self.vault.set_password(text)
                    self.pantha_mode = True
                    self.update_header()
                    self.update_status("Vault Unlocked")
                    self.log.write("[green]Vault password set and vault unlocked![/]")
                    self.awaiting_password_setup = False
                    self._first_pass = None
        else:
            if text:
                self.command_history.append(text)
                self.history_index = len(self.command_history)
                self.run_command(text)

    # =====================================================
    # COMMAND HANDLING
    # =====================================================
    def run_command(self, cmd: str):
        parts = shlex_split(cmd)
        if not parts:
            return
        c = parts[0].lower()

        log = self.log
        vault = self.vault

        # ---------------- HELP ----------------
        if c == "help":
            log.write("[bold cyan]Commands:[/]")
            log.write("note list | note create <title> | note view <title> | note delete <title>")
            log.write("note append <title> <text> | note rename <old> <new> | note pin <title> | note unpin <title> | note pinned")
            log.write("search <query> | history | clear | exit | lock | status")
            return

        # ---------------- EXIT ----------------
        if c in ("exit", "quit"):
            self.exit()
            return

        # ---------------- LOCK ----------------
        if c == "lock":
            vault.lock()
            self.pantha_mode = False
            self.update_header()
            self.update_status("Locked")
            log.write("[yellow]Vault locked[/]")
            return

        # ---------------- STATUS ----------------
        if c == "status":
            log.write("[green]Unlocked[/]" if self.pantha_mode else "[yellow]Locked[/]")
            return

        # ---------------- NOTE COMMANDS ----------------
        if c == "note":
            if not self.pantha_mode:
                log.write("[red]Unlock vault first[/]")
                return
            self.handle_note(parts)
            return

        # ---------------- SEARCH ----------------
        if c == "search":
            if not self.pantha_mode:
                log.write("[red]Unlock vault first[/]")
                return
            query = " ".join(parts[1:]).lower()
            results = [meta['title'] for meta in vault.list_notes().values() if query in meta['title'].lower()]
            if results:
                for r in results:
                    pin = "📌 " if r in self.pins else ""
                    log.write(f"{pin}{r}")
            else:
                log.write("[yellow]No matching notes found[/]")
            return

        # ---------------- HISTORY ----------------
        if c == "history":
            for i, h in enumerate(self.command_history[-50:], 1):
                log.write(f"{i}. {h}")
            return

        # ---------------- CLEAR ----------------
        if c == "clear":
            log.clear()
            return

        log.write("[red]Unknown command[/]")

    # =====================================================
    # NOTE HANDLER
    # =====================================================
    def handle_note(self, parts):
        log = self.log
        vault = self.vault
        if len(parts) < 2:
            return
        action = parts[1]

        try:
            if action == "list":
                for meta in vault.list_notes().values():
                    pin = "📌 " if meta["title"] in self.pins else ""
                    log.write(f"{pin}{meta['title']}")
                return
            if action == "create":
                vault.create_note(parts[2], "")
                log.write("[green]Note created[/]")
                return
            if action == "view":
                log.write(vault.read_note_by_title(parts[2]))
                return
            if action == "delete":
                vault.delete_note_by_title(parts[2])
                self.pins.discard(parts[2])
                self.save_pins()
                log.write("[yellow]Note deleted[/]")
                return
            if action == "append":
                title = parts[2]
                text = " ".join(parts[3:])
                old = vault.read_note_by_title(title)
                vault.update_note_by_title(title, old + "\n" + text)
                log.write("[green]Note updated[/]")
                return
            if action == "rename":
                old, new = parts[2], parts[3]
                txt = vault.read_note_by_title(old)
                vault.delete_note_by_title(old)
                vault.create_note(new, txt)
                if old in self.pins:
                    self.pins.discard(old)
                    self.pins.add(new)
                    self.save_pins()
                log.write("[green]Note renamed[/]")
                return
            if action == "pin":
                self.pins.add(parts[2])
                self.save_pins()
                log.write("[green]Note pinned[/]")
                return
            if action == "unpin":
                self.pins.discard(parts[2])
                self.save_pins()
                log.write("[yellow]Note unpinned[/]")
                return
            if action == "pinned":
                for p in self.pins:
                    log.write(f"📌 {p}")
                return
        except VaultError as e:
            log.write(f"[red]{e}[/]")

    # =====================================================
    # HISTORY NAVIGATION
    # =====================================================
    def action_history_prev(self):
        if not self.command_history:
            return
        self.history_index = max(0, self.history_index - 1)
        self.input_widget.value = self.command_history[self.history_index]

    def action_history_next(self):
        if not self.command_history:
            return
        self.history_index = min(len(self.command_history)-1, self.history_index + 1)
        self.input_widget.value = self.command_history[self.history_index]

    # =====================================================
    # HOTKEYS
    # =====================================================
    def action_clear_log(self):
        self.log.clear()

    def action_quit_app(self):
        self.exit()

    def action_focus_input(self):
        self.focus_input()

    def action_list_notes(self):
        if self.pantha_mode:
            self.run_command("note list")
        else:
            self.log.write("[red]Unlock vault first[/]")

    def action_search_notes(self):
        if self.pantha_mode:
            self.run_command("search ")
        else:
            self.log.write("[red]Unlock vault first[/]")

    # =====================================================
    # HISTORY & PIN FILES
    # =====================================================
    def load_history(self):
        if HISTORY_FILE.exists():
            self.command_history = json.loads(HISTORY_FILE.read_text())

    def save_history(self):
        HISTORY_FILE.write_text(json.dumps(self.command_history, indent=2))

    def load_pins(self):
        if PIN_FILE.exists():
            self.pins = set(json.loads(PIN_FILE.read_text()))

    def save_pins(self):
        PIN_FILE.write_text(json.dumps(list(self.pins), indent=2))

# =====================================================
# ENTRY POINT
# =====================================================
if __name__ == "__main__":
    PanthaTerminal().run()
