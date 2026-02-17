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


# =========================================================
# PATHS
# =========================================================

def user_data_dir() -> Path:
    path = Path.home() / ".pantha"
    path.mkdir(parents=True, exist_ok=True)
    return path

DATA_DIR = user_data_dir()
HISTORY_FILE = DATA_DIR / "history.json"
PIN_FILE = DATA_DIR / "pins.json"


# =========================================================
# BANNER
# =========================================================

class PanthaBanner(Static):
    def on_mount(self) -> None:
        self.update(
r"""
██████   █████  ███    ██ ████████ ██   ██  █████
██   ██ ██   ██ ████   ██    ██    ██   ██ ██   ██
██████  ███████ ██ ██  ██    ██    ███████ ███████      --  ENCRYPTED & SECURE NOTE-BASED TERMINAL
██      ██   ██ ██  ██ ██    ██    ██   ██ ██   ██                 BROUGHT TO YOU BY:  ™ V1LE-CODE
██      ██   ██ ██   ████    ██    ██   ██ ██   ██
"""
        )


# =========================================================
# TERMINAL APP
# =========================================================

class PanthaTerminal(App):

    TITLE = "Pantha Terminal"
    SUB_TITLE = "Official Pantha Terminal v1.2.3"

    DEFAULT_BINDINGS = False
    
    # 🔥 disables ctrl+p palette
    COMMAND_PALETTE = False
    
    BINDINGS = [
        ("ctrl+l", "clear_log", "Clear"),
        ("ctrl+q", "quit_app", "Quit"),
        ("ctrl+i", "focus_input", "Focus Input"),
        ("ctrl+n", "list_notes", "Notes"),
        ("up", "history_prev", "Prev Cmd"),
        ("down", "history_next", "Next Cmd"),
    ]

    CSS = """
    Screen { background: #020005; color: #eadcff; }
    #log { background: #1a001f; }
    Input { background: #120017; border: round #aa00ff; }
    #status_line { background: #120017; color: #00ff3c; }
    Header { background: #1a001f; }
    Footer { background: #1a001f; }
    """

    status_text: reactive[str] = reactive("Ready")

    # -----------------------------------------------------

    def __init__(self):
        super().__init__()
        self.vault: Vault | None = None
        self.pantha_mode = False
        self.command_history: list[str] = []
        self.history_index = -1

        self.username = os.environ.get("USERNAME") or os.environ.get("USER") or "pantha"
        self.hostname = os.environ.get("COMPUTERNAME") or "local"

        self.load_history()
        self.load_pins()

    # =====================================================
    # UI
    # =====================================================

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield PanthaBanner()
        with ScrollableContainer():
            yield RichLog(id="log", markup=True, wrap=True)
        yield Static("", id="status_line")
        yield Input(id="command_input", placeholder="Enter command...")
        yield Footer()

    def on_mount(self):
        log = self.query_one("#log", RichLog)
        log.write("[bold #a366ff]Pantha Terminal Ready[/]")
        log.write("Type [bold]help[/] for assistance")
        self.focus_input()

    def focus_input(self):
        self.query_one("#command_input", Input).focus()

    # =====================================================
    # HOTKEY ACTIONS
    # =====================================================

    def action_clear_log(self):
        self.query_one("#log", RichLog).clear()

    def action_show_help(self):
        self.run_command_safe("help")

    def action_quit_app(self):
        self.exit()

    def action_focus_input(self):
        self.focus_input()

    def action_show_pins(self):
        if not self.pantha_mode:
            self.log_write("Unlock vault first")
            return
        self.run_command_safe("note pinned")

    def action_list_notes(self):
        if not self.pantha_mode:
            self.log_write("Unlock vault first")
            return
        self.run_command_safe("note list")

    def action_history_prev(self):
        if not self.command_history:
            return
        self.history_index = max(0, self.history_index - 1)
        self.query_one("#command_input", Input).value = self.command_history[self.history_index]

    def action_history_next(self):
        if not self.command_history:
            return
        self.history_index = min(len(self.command_history)-1, self.history_index + 1)
        self.query_one("#command_input", Input).value = self.command_history[self.history_index]

    # =====================================================
    # INPUT
    # =====================================================

    def on_input_submitted(self, event: Input.Submitted):
        cmd = event.value.strip()
        event.input.value = ""
        self.history_index = len(self.command_history)
        self.run_command_safe(cmd)
        self.focus_input()

    # =====================================================
    # HISTORY
    # =====================================================

    def load_history(self):
        if HISTORY_FILE.exists():
            self.command_history = json.loads(HISTORY_FILE.read_text())

    def save_history(self):
        HISTORY_FILE.write_text(json.dumps(self.command_history, indent=2))

    # =====================================================
    # PINS
    # =====================================================

    def load_pins(self):
        if PIN_FILE.exists():
            self.pins = set(json.loads(PIN_FILE.read_text()))
        else:
            self.pins = set()

    def save_pins(self):
        PIN_FILE.write_text(json.dumps(list(self.pins), indent=2))

    # =====================================================
    # LOG HELPER
    # =====================================================

    def log_write(self, text: str):
        self.query_one("#log", RichLog).write(text)

    # =====================================================
    # COMMAND SAFE
    # =====================================================

    def run_command_safe(self, cmd: str):
        log = self.query_one("#log", RichLog)
        log.write(f"[#7c33ff]{self.username}@{self.hostname}[/] $ {escape(cmd)}")

        try:
            self.command_history.append(cmd)
            self.save_history()
            self.run_command(cmd)
        except Exception:
            log.write("[bold red]INTERNAL ERROR[/]")
            log.write(escape(traceback.format_exc()))

    # =====================================================
    # COMMAND ROUTER
    # =====================================================

    def run_command(self, cmd: str):

        log = self.query_one("#log", RichLog)
        parts = shlex_split(cmd)
        if not parts:
            return

        c = parts[0].lower()

        # ---------------- HELP ----------------
        if c == "help":
            log.write("""
[bold #a366ff]COMMANDS[/]

[#a366ff]unlock[/] [#888888]<pass>
[#a366ff]lock[/]
[#a366ff]passwd[/] [#888888]<old> <new>
[#a366ff]status[/]

[#a366ff]note[/] list
[#a366ff]note[/] create [#888888]<title>[/]
[#a366ff]note[/] view [#888888]<title>[/]
[#a366ff]note[/] delete [#888888]<title>[/]
[#a366ff]note[/] append [#888888]<title> <text>[/]
[#a366ff]note[/] rename [#888888]<old> <new>[/]
[#a366ff]note[/] search [#888888]<word>[/]
[#a366ff]note[/] pin [#888888]<title>[/]
[#a366ff]note[/] unpin [#888888]<title>[/]
[#a366ff]note[/] pinned

[#a366ff]history[/]
[#a366ff]clear[/]
[#a366ff]exit[/]

[bold #a366ff]HOTKEYS[/]
[#888888]Ctrl+L clear
Ctrl+H help
Ctrl+Q quit
Ctrl+P pinned
Ctrl+N list notes
↑ ↓ history[/]
""")
            return

        # ---------------- UNLOCK ----------------
        if c == "unlock":
            if len(parts) < 2:
                log.write("Usage: unlock <password>")
                return

            self.vault = Vault(str(DATA_DIR))
            try:
                self.vault.unlock(parts[1])
                self.pantha_mode = True
                log.write("[green]Vault unlocked[/]")
                self.update_status("Unlocked")
            except Exception:
                log.write("[red]Unlock failed[/]")
            return

        # ---------------- LOCK ----------------
        if c == "lock":
            if self.vault:
                self.vault.lock()
                self.pantha_mode = False
                log.write("Vault locked")
                self.update_status("Locked")
            return

        # ---------------- STATUS ----------------
        if c == "status":
            log.write("[green]Vault unlocked[/]" if self.pantha_mode else "[yellow]Vault locked[/]")
            return

        # ---------------- NOTES ----------------
        if c == "note":
            if not self.pantha_mode:
                log.write("Unlock vault first")
                return
            self.handle_note(parts)
            return

        # ---------------- HISTORY ----------------
        if c == "history":
            for i, cmd in enumerate(self.command_history[-20:], 1):
                log.write(f"{i}. {cmd}")
            return

        # ---------------- CLEAR ----------------
        if c == "clear":
            log.clear()
            return

        # ---------------- EXIT ----------------
        if c in ("exit", "quit"):
            self.exit()
            return

        log.write("Unknown command")

    # =====================================================
    # NOTE COMMANDS
    # =====================================================

    def handle_note(self, parts):

        log = self.query_one("#log", RichLog)

        if len(parts) < 2:
            return

        action = parts[1]
        vault = self.vault

        try:

            if action == "list":
                notes = vault.list_notes()
                for i, meta in notes.items():
                    pin = "📌 " if meta["title"] in self.pins else ""
                    log.write(f"{pin}{meta['title']}")
                return

            if action == "create":
                title = parts[2]
                vault.create_note(title, "")
                log.write("Created")
                return

            if action == "view":
                log.write(vault.read_note_by_title(parts[2]))
                return

            if action == "delete":
                title = parts[2]
                vault.delete_note_by_title(title)
                self.pins.discard(title)
                self.save_pins()
                log.write("Deleted")
                return

            if action == "append":
                title = parts[2]
                text = " ".join(parts[3:])
                old = vault.read_note_by_title(title)
                vault.update_note_by_title(title, old + "\n" + text)
                log.write("Updated")
                return

            if action == "rename":
                old, new = parts[2], parts[3]
                text = vault.read_note_by_title(old)
                vault.delete_note_by_title(old)
                vault.create_note(new, text)

                if old in self.pins:
                    self.pins.remove(old)
                    self.pins.add(new)
                    self.save_pins()

                log.write("Renamed")
                return

            if action == "search":
                word = " ".join(parts[2:])
                notes = vault.list_notes()
                for meta in notes.values():
                    if word.lower() in vault.read_note_by_title(meta["title"]).lower():
                        log.write(meta["title"])
                return

            if action == "pin":
                title = parts[2]
                self.pins.add(title)
                self.save_pins()
                log.write("Pinned")
                return

            if action == "unpin":
                title = parts[2]
                self.pins.discard(title)
                self.save_pins()
                log.write("Unpinned")
                return

            if action == "pinned":
                if not self.pins:
                    log.write("No pinned notes")
                    return
                for p in self.pins:
                    log.write(f"📌 {p}")
                return

        except VaultError as e:
            log.write(str(e))

    # =====================================================
    # STATUS BAR
    # =====================================================

    def update_status(self, text: str):
        self.query_one("#status_line", Static).update(f"STATUS: {text}")


# =====================================================
# ENTRY
# =====================================================

if __name__ == "__main__":
    PanthaTerminal().run()
