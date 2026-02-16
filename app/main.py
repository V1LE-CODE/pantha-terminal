from __future__ import annotations
import os
import json
import traceback
import time
from pathlib import Path
from shlex import split as shlex_split
from typing import Dict, List

from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer, Horizontal, Vertical
from textual.widgets import Header, Footer, Input, Static, RichLog, TextArea
from textual.reactive import reactive
from textual.timer import Timer
from rich.markup import escape
from rich.syntax import Syntax
from rich.panel import Panel
from rich.markdown import Markdown

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
CURSOR_FILE = DATA_DIR / "cursor.json"


# =========================================================
# BANNER
# =========================================================

class PanthaBanner(Static):
    def on_mount(self) -> None:
        self.update(
r"""
██████   █████  ███    ██ ████████ ██   ██  █████
██   ██ ██   ██ ████   ██    ██    ██   ██ ██   ██
██████  ███████ ██ ██  ██    ██    ███████ ███████
██      ██   ██ ██  ██ ██    ██    ██   ██ ██   ██
██      ██   ██ ██   ████    ██    ██   ██ ██   ██
"""
        )


# =========================================================
# TAB SYSTEM
# =========================================================

class EditorTab:
    def __init__(self, title: str, content: str = ""):
        self.title = title
        self.content = content
        self.undo_stack: List[str] = []
        self.redo_stack: List[str] = []
        self.cursor = 0
        self.read_only = False
        self.preview = False
        self.syntax = False


# =========================================================
# MAIN APP
# =========================================================

class PanthaTerminal(App):

    TITLE = "Pantha Terminal"
    SUB_TITLE = "Encrypted Note Environment"

    BINDINGS = [
        ("ctrl+q", "quit_app", "Quit"),
        ("ctrl+l", "clear_log", "Clear"),
        ("ctrl+h", "help", "Help"),
        ("ctrl+s", "save", "Save"),
        ("ctrl+z", "undo", "Undo"),
        ("ctrl+y", "redo", "Redo"),
        ("ctrl+t", "new_tab", "New Tab"),
        ("ctrl+w", "close_tab", "Close Tab"),
        ("ctrl+tab", "next_tab", "Next Tab"),
        ("ctrl+shift+tab", "prev_tab", "Prev Tab"),
        ("ctrl+p", "toggle_preview", "Preview"),
        ("ctrl+r", "toggle_readonly", "Readonly"),
        ("ctrl+e", "toggle_syntax", "Syntax"),
        ("ctrl+i", "focus_input", "Input"),
    ]

    CSS = """
    Screen { background: #020005; color: #eadcff; }
    #log { background: #1a001f; height: 1fr; }
    Input { background: #120017; border: round #aa00ff; }
    #status { background: #120017; color: #00ffcc; height:1; }
    TextArea { background:#0a0010; }
    """

    status_text: reactive[str] = reactive("Ready")

    # -----------------------------------------------------

    def __init__(self):
        super().__init__()

        self.vault: Vault | None = None
        self.pantha_mode = False

        self.command_history: list[str] = []
        self.history_index = -1

        self.tabs: List[EditorTab] = []
        self.current_tab = -1

        self.autosave_timer: Timer | None = None

        self.load_history()
        self.load_pins()
        self.load_cursor_memory()

    # =====================================================
    # UI
    # =====================================================

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield PanthaBanner()

        with Horizontal():
            with Vertical():
                yield RichLog(id="log", markup=True, wrap=True)
                yield Input(id="command", placeholder="command...")
            yield TextArea(id="editor")

        yield Static("STATUS: Ready", id="status")
        yield Footer()

    def on_mount(self):
        self.log("Pantha ready. Type help.")
        self.focus_input()
        self.autosave_timer = self.set_interval(5, self.autosave)

    # =====================================================
    # UTIL
    # =====================================================

    def log(self, text: str):
        self.query_one("#log", RichLog).write(text)

    def status(self, text: str):
        self.query_one("#status", Static).update("STATUS: " + text)

    def editor(self) -> TextArea:
        return self.query_one("#editor", TextArea)

    def current(self) -> EditorTab | None:
        if 0 <= self.current_tab < len(self.tabs):
            return self.tabs[self.current_tab]
        return None

    # =====================================================
    # HISTORY
    # =====================================================

    def load_history(self):
        if HISTORY_FILE.exists():
            self.command_history = json.loads(HISTORY_FILE.read_text())

    def save_history(self):
        HISTORY_FILE.write_text(json.dumps(self.command_history))

    # =====================================================
    # CURSOR MEMORY
    # =====================================================

    def load_cursor_memory(self):
        if CURSOR_FILE.exists():
            self.cursor_memory = json.loads(CURSOR_FILE.read_text())
        else:
            self.cursor_memory = {}

    def save_cursor_memory(self):
        CURSOR_FILE.write_text(json.dumps(self.cursor_memory))

    # =====================================================
    # PINS
    # =====================================================

    def load_pins(self):
        if PIN_FILE.exists():
            self.pins = set(json.loads(PIN_FILE.read_text()))
        else:
            self.pins = set()

    def save_pins(self):
        PIN_FILE.write_text(json.dumps(list(self.pins)))

    # =====================================================
    # INPUT
    # =====================================================

    def on_input_submitted(self, e: Input.Submitted):
        cmd = e.value.strip()
        e.input.value = ""
        self.run_command_safe(cmd)

    def focus_input(self):
        self.query_one("#command", Input).focus()

    # =====================================================
    # AUTOSAVE
    # =====================================================

    def autosave(self):
        tab = self.current()
        if not tab or not self.pantha_mode:
            return
        if not self.vault:
            return
        try:
            self.vault.update_note_by_title(tab.title, tab.content)
            self.status("Autosaved")
        except Exception:
            pass

    # =====================================================
    # TAB MANAGEMENT
    # =====================================================

    def action_new_tab(self):
        self.tabs.append(EditorTab("untitled"))
        self.current_tab = len(self.tabs)-1
        self.refresh_editor()

    def action_close_tab(self):
        if self.current_tab >= 0:
            self.tabs.pop(self.current_tab)
            self.current_tab -= 1
            self.refresh_editor()

    def action_next_tab(self):
        if self.tabs:
            self.current_tab = (self.current_tab + 1) % len(self.tabs)
            self.refresh_editor()

    def action_prev_tab(self):
        if self.tabs:
            self.current_tab = (self.current_tab - 1) % len(self.tabs)
            self.refresh_editor()

    def refresh_editor(self):
        ed = self.editor()
        tab = self.current()
        if not tab:
            ed.value = ""
            return
        ed.value = tab.content
        ed.cursor_position = tab.cursor
        self.status(f"Tab: {tab.title}")

    # =====================================================
    # EDITOR EVENTS
    # =====================================================

    def on_text_area_changed(self, e: TextArea.Changed):
        tab = self.current()
        if not tab or tab.read_only:
            return
        tab.undo_stack.append(tab.content)
        tab.content = e.text
        tab.cursor = e.cursor_position

    # =====================================================
    # UNDO / REDO
    # =====================================================

    def action_undo(self):
        tab = self.current()
        if tab and tab.undo_stack:
            tab.redo_stack.append(tab.content)
            tab.content = tab.undo_stack.pop()
            self.refresh_editor()

    def action_redo(self):
        tab = self.current()
        if tab and tab.redo_stack:
            tab.undo_stack.append(tab.content)
            tab.content = tab.redo_stack.pop()
            self.refresh_editor()

    # =====================================================
    # TOGGLES
    # =====================================================

    def action_toggle_preview(self):
        tab = self.current()
        if not tab:
            return
        tab.preview = not tab.preview
        if tab.preview:
            self.show_preview(tab)
        else:
            self.refresh_editor()

    def show_preview(self, tab: EditorTab):
        md = Markdown(tab.content)
        self.query_one("#editor", TextArea).visible = False
        self.mount(Static(md, id="preview"))

    def action_toggle_readonly(self):
        tab = self.current()
        if tab:
            tab.read_only = not tab.read_only
            self.status("Readonly ON" if tab.read_only else "Readonly OFF")

    def action_toggle_syntax(self):
        tab = self.current()
        if tab:
            tab.syntax = not tab.syntax
            if tab.syntax:
                code = Syntax(tab.content, "python", theme="monokai", line_numbers=True)
                self.mount(Static(Panel(code), id="syntax"))
            else:
                self.refresh_editor()

    # =====================================================
    # HOTKEY ACTIONS
    # =====================================================

    def action_clear_log(self):
        self.query_one("#log", RichLog).clear()

    def action_quit_app(self):
        self.save_cursor_memory()
        self.exit()

    def action_help(self):
        self.run_command_safe("help")

    def action_save(self):
        tab = self.current()
        if tab and self.vault:
            self.vault.update_note_by_title(tab.title, tab.content)
            self.status("Saved")

    # =====================================================
    # COMMAND SAFE
    # =====================================================

    def run_command_safe(self, cmd: str):
        self.log(f"> {escape(cmd)}")
        try:
            self.command_history.append(cmd)
            self.save_history()
            self.run_command(cmd)
        except Exception:
            self.log("[red]ERROR[/]")
            self.log(escape(traceback.format_exc()))

    # =====================================================
    # COMMAND ROUTER
    # =====================================================

    def run_command(self, cmd: str):

        parts = shlex_split(cmd)
        if not parts:
            return
        c = parts[0]

        # HELP
        if c == "help":
            self.log("""
unlock <pass>
lock
note list/create/view/delete
tab new/close
""")
            return

        # UNLOCK
        if c == "unlock":
            self.vault = Vault(str(DATA_DIR))
            self.vault.unlock(parts[1])
            self.pantha_mode = True
            self.status("Unlocked")
            return

        if c == "lock":
            if self.vault:
                self.vault.lock()
                self.pantha_mode = False
                self.status("Locked")
            return

        # NOTES
        if c == "note":
            self.handle_note(parts)
            return

        if c == "tab":
            if parts[1] == "new":
                self.action_new_tab()
            elif parts[1] == "close":
                self.action_close_tab()
            return

        self.log("Unknown command")

    # =====================================================
    # NOTE COMMANDS
    # =====================================================

    def handle_note(self, parts):

        if not self.pantha_mode:
            self.log("Unlock vault first")
            return

        vault = self.vault

        try:
            cmd = parts[1]

            if cmd == "list":
                for meta in vault.list_notes().values():
                    self.log(meta["title"])

            elif cmd == "create":
                title = parts[2]
                vault.create_note(title, "")
                self.tabs.append(EditorTab(title))
                self.current_tab = len(self.tabs)-1
                self.refresh_editor()

            elif cmd == "view":
                title = parts[2]
                text = vault.read_note_by_title(title)
                self.tabs.append(EditorTab(title, text))
                self.current_tab = len(self.tabs)-1
                self.refresh_editor()

            elif cmd == "delete":
                vault.delete_note_by_title(parts[2])
                self.log("Deleted")

        except VaultError as e:
            self.log(str(e))


# =====================================================
# ENTRY
# =====================================================

if __name__ == "__main__":
    PanthaTerminal().run()
