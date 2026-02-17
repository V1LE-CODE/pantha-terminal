from __future__ import annotations
import os
import json
import traceback
from pathlib import Path
from shlex import split as shlex_split

from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Header, Input, Static, RichLog
from textual.reactive import reactive
from rich.markup import escape

from vault import Vault, VaultError


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
# ASCII BANNER
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
# CUSTOM STATUS BAR
# =========================================================

class StatusBar(Static):
    def set(self, text: str):
        self.update(f" STATUS ▸ {text} ")


# =========================================================
# TERMINAL
# =========================================================

class PanthaTerminal(App):

    TITLE = "Pantha Terminal"
    SUB_TITLE = "Official Pantha Terminal v1.2.3"

    ENABLE_COMMAND_PALETTE = False

    CSS = """
    Screen {
        background: #020005;
        color: #eadcff;
    }

    Header {
        background: #1a001f;
    }

    #log {
        background: #1a001f;
    }

    Input {
        background: #120017;
        border: round #aa00ff;
    }

    #statusbar {
        dock: bottom;
        height: 1;
        background: #120017;
        color: #00ff9c;
        content-align: left middle;
    }
    """

    BINDINGS = [
        ("ctrl+l", "clear_log", "Clear"),
        ("ctrl+q", "quit_app", "Quit"),
        ("ctrl+i", "focus_input", "Focus"),
        ("ctrl+n", "list_notes", "Notes"),
        ("up", "history_prev", ""),
        ("down", "history_next", ""),
    ]

    status_text: reactive[str] = reactive("Ready")

    # =====================================================

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
    # BLOCK PALETTE
    # =====================================================

    def on_key(self, event):
        if event.key == "ctrl+p":
            event.stop()

    def action_command_palette(self):
        pass

    # =====================================================
    # UI
    # =====================================================

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield PanthaBanner()

        with ScrollableContainer():
            yield RichLog(id="log", markup=True, wrap=True)

        yield Input(id="command_input", placeholder="Enter command...")
        yield StatusBar(id="statusbar")

    def on_mount(self):
        log = self.query_one("#log", RichLog)
        log.write("[bold #a366ff]Pantha Terminal Ready[/]")
        log.write("Type [bold]help[/] for commands")
        self.focus_input()
        self.update_status("Ready")

    def focus_input(self):
        self.query_one("#command_input", Input).focus()

    # =====================================================
    # HOTKEYS
    # =====================================================

    def action_clear_log(self):
        self.query_one("#log", RichLog).clear()

    def action_quit_app(self):
        self.exit()

    def action_focus_input(self):
        self.focus_input()

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
    # LOG
    # =====================================================

    def log_write(self, text: str):
        self.query_one("#log", RichLog).write(text)

    # =====================================================
    # SAFE EXEC
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

        if c == "help":
            log.write("""
[bold #a366ff]COMMANDS[/]

unlock <pass>
lock
status

note list
note create <title>
note view <title>
note delete <title>
note append <title> <text>
note rename <old> <new>
note pin <title>
note unpin <title>
note pinned

history
clear
exit
""")
            return

        if c == "unlock":
            if len(parts) < 2:
                log.write("Usage: unlock <password>")
                return
            self.vault = Vault(str(DATA_DIR))
            try:
                self.vault.unlock(parts[1])
                self.pantha_mode = True
                log.write("[green]Vault unlocked[/]")
                self.update_status("Vault Unlocked")
            except Exception:
                log.write("[red]Unlock failed[/]")
                self.update_status("Unlock Failed")
            return

        if c == "lock":
            if self.vault:
                self.vault.lock()
                self.pantha_mode = False
                log.write("Vault locked")
                self.update_status("Locked")
            return

        if c == "status":
            log.write("[green]Unlocked[/]" if self.pantha_mode else "[yellow]Locked[/]")
            return

        if c == "note":
            if not self.pantha_mode:
                log.write("Unlock vault first")
                return
            self.handle_note(parts)
            return

        if c == "history":
            for i, cmd in enumerate(self.command_history[-20:], 1):
                log.write(f"{i}. {cmd}")
            return

        if c == "clear":
            log.clear()
            return

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
                for meta in vault.list_notes().values():
                    pin = "📌 " if meta["title"] in self.pins else ""
                    log.write(f"{pin}{meta['title']}")
                return

            if action == "create":
                vault.create_note(parts[2], "")
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
                txt = vault.read_note_by_title(old)
                vault.delete_note_by_title(old)
                vault.create_note(new, txt)
                log.write("Renamed")
                return

            if action == "pin":
                self.pins.add(parts[2])
                self.save_pins()
                log.write("Pinned")
                return

            if action == "unpin":
                self.pins.discard(parts[2])
                self.save_pins()
                log.write("Unpinned")
                return

            if action == "pinned":
                for p in self.pins:
                    log.write(f"📌 {p}")
                return

        except VaultError as e:
            log.write(str(e))

    # =====================================================
    # STATUS BAR UPDATE
    # =====================================================

    def update_status(self, text: str):
        self.query_one("#statusbar", StatusBar).set(text)


# =====================================================
# ENTRY
# =====================================================

if __name__ == "__main__":
    PanthaTerminal().run()
